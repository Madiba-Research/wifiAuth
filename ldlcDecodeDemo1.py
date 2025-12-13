import numpy as np
from scipy import signal
from scipy.fft import fft, ifft

# this is better than ldlcDecodedemo, and faster

class LDLCDecoder:
    """
    低密度格码（LDLC）迭代解码器
    """
    
    def __init__(self, H, sigma2, resolution=1/16, pdf_range=10.0):
        """
        初始化LDLC解码器
        """
        self.H = H
        self.n = H.shape[0]
        self.sigma2 = sigma2
        self.sigma = np.sqrt(sigma2)
        self.delta = resolution
        self.pdf_range = pdf_range
        
        # PDF的采样点数量
        self.L = int(pdf_range / resolution)
        
        # 构建二部图结构
        self._build_bipartite_graph()
        
        # print(f"解码器初始化: n={self.n}, σ²={sigma2:.4f}, L={self.L}")
        # print(f"二部图: {len(self.edges)} 条边")
        
    def _build_bipartite_graph(self):
        """构建二部图：变量节点和校验节点之间的连接"""
        self.edges = {}  # {(var_node, check_node): weight}
        self.var_to_check = [[] for _ in range(self.n)]
        self.check_to_var = [[] for _ in range(self.n)]
        
        for i in range(self.n):  # 校验节点（行）
            for j in range(self.n):  # 变量节点（列）
                if abs(self.H[i, j]) > 1e-10:
                    self.edges[(j, i)] = self.H[i, j]
                    self.var_to_check[j].append(i)
                    self.check_to_var[i].append(j)

        # print(self.var_to_check)
        # print(self.check_to_var)
        
        # 打印图结构信息
        degrees = [len(self.var_to_check[i]) for i in range(self.n)]
        # print(f"变量节点度数: min={min(degrees)}, max={max(degrees)}, avg={np.mean(degrees):.1f}")
    
    def _create_pdf_grid(self, center, range_size):
        """创建以center为中心的PDF网格"""
        half_range = range_size / 2
        return np.linspace(center - half_range, center + half_range, self.L)
    
    def _gaussian_pdf(self, x_grid, mean, variance):
        """在给定网格上计算高斯PDF"""
        if variance < 1e-10:
            variance = 1e-10
        return np.exp(-((x_grid - mean) ** 2) / (2 * variance)) / np.sqrt(2 * np.pi * variance)
    
    def _resample_pdf_1(self, pdf, old_grid, new_grid):
        """将PDF从旧网格重采样到新网格"""
        # 使用线性插值
        resampled = np.interp(new_grid, old_grid, pdf, left=0, right=0)
        # 归一化
        total = np.sum(resampled) * (new_grid[1] - new_grid[0])
        if total > 1e-10:
            resampled /= total
        return resampled
    

    def _resample_pdf(self, pdf, old_grid, new_grid):
        """将PDF从旧网格重采样到新网格"""
        # 检查输入有效性
        if len(old_grid) < 2 or len(pdf) != len(old_grid):
            # 返回均匀分布
            result = np.ones(len(new_grid)) / len(new_grid)
            return result
        
        # 使用线性插值
        resampled = np.interp(new_grid, old_grid, pdf, left=0, right=0)
        # 归一化
        total = np.sum(resampled) * (new_grid[1] - new_grid[0])
        if total > 1e-10:
            resampled /= total
        else:
            # 如果总质量太小，返回均匀分布
            resampled = np.ones(len(new_grid)) / len(new_grid)
        return resampled
    

    def _convolve_pdfs_2(self, pdf1, grid1, pdf2, grid2):
        """
        快速卷积两个 PDF（FFT），返回 (conv_pdf, conv_grid)。
        1. 对称重采样：两个 PDF 都插值到同一套更精细的网格；
        2. 归一化使用卷积后真实步长；
        3. 若总质量≈0，返回零向量而非均匀分布，避免支撑集漂移。
        """
        # ---------- 1. 决定公共网格 ----------
        delta1 = grid1[1] - grid1[0]
        delta2 = grid2[1] - grid2[0]
        delta  = min(delta1, delta2)                # 选更精细的步长
        g_min  = min(grid1[0],  grid2[0])
        g_max  = max(grid1[-1], grid2[-1])
        # 让点数对齐到 2 的幂，方便 FFT
        n = 2 ** int(np.ceil(np.log2((g_max - g_min) / delta + 1)))
        common_grid = np.linspace(g_min, g_max, n)
        delta = common_grid[1] - common_grid[0]     # 实际步长

        # ---------- 2. 插值到公共网格 ----------
        def safe_interp(y, x, x_new):
            # 区域外给 0，避免外推
            return np.interp(x_new, x, y, left=0.0, right=0.0)

        p1 = safe_interp(pdf1, grid1, common_grid)
        p2 = safe_interp(pdf2, grid2, common_grid)

        # ---------- 3. FFT 卷积 ----------
        conv = signal.fftconvolve(p1, p2, mode='full') * delta

        # ---------- 4. 卷积后的自然网格 ----------
        c_min = grid1[0] + grid2[0]
        c_max = grid1[-1] + grid2[-1]
        conv_grid_nat = np.linspace(c_min, c_max, len(conv))

        # ---------- 5. 重采样到标准长度 ----------
        if len(conv) != self.L:
            c_center = (c_min + c_max) / 2
            target_grid = self._create_pdf_grid(c_center, self.pdf_range)
            conv = np.interp(target_grid, conv_grid_nat, conv, left=0.0, right=0.0)
            conv_grid = target_grid
        else:
            conv_grid = conv_grid_nat

        # ---------- 6. 归一化 ----------
        total = np.sum(conv)
        if total > 1e-12:
            conv /= total
        # 否则保持全 0，调用方可按需处理

        return conv, conv_grid
    

    def _convolve_pdfs_1(self, pdf1, grid1, pdf2, grid2):
        """卷积两个 PDF，统一用 FFT，插值仅 2 次"""
        # 1. 目标网格
        new_min = grid1[0] + grid2[0]
        new_max = grid1[-1] + grid2[-1]
        new_grid = np.linspace(new_min, new_max, self.L)

        # 2. 构造一条“足够密”的公共均匀网格
        #    步长取两者最小步长，或再除以 2 防止信息丢失
        delta1 = grid1[1] - grid1[0]
        delta2 = grid2[1] - grid2[0]
        delta = min(delta1, delta2) / 2.0
        common_grid = np.arange(new_min, new_max + delta, delta)

        # 3. 把两条 PDF 插值到公共网格
        pdf1_rs = np.interp(common_grid, grid1, pdf1, left=0, right=0)
        pdf2_rs = np.interp(common_grid, grid2, pdf2, left=0, right=0)

        # 4. FFT 卷积
        conv = signal.fftconvolve(pdf1_rs, pdf2_rs, mode='full') * delta

        # 5. 构造卷积后的网格
        conv_grid = np.linspace(grid1[0] + grid2[0],
                                grid1[-1] + grid2[-1],
                                len(conv))

        # 6. 重采样到最终长度
        result = self._resample_pdf(conv, conv_grid, new_grid)
        return result, new_grid
    

    def _convolve_pdfs(self, pdf1, grid1, pdf2, grid2):
        """卷积两个 PDF，统一用 FFT，插值仅 2 次"""
        # 1. 目标网格
        new_min = grid1[0] + grid2[0]
        new_max = grid1[-1] + grid2[-1]
        new_grid = np.linspace(new_min, new_max, self.L)

        # 2. 构造一条"足够密"的公共均匀网格
        #    步长取两者最小步长，或再除以 2 防止信息丢失
        delta1 = grid1[1] - grid1[0] if len(grid1) > 1 else self.delta
        delta2 = grid2[1] - grid2[0] if len(grid2) > 1 else self.delta
        delta = min(delta1, delta2) / 2.0
        
        # 确保至少有一些采样点
        if delta <= 0:
            delta = self.delta
        
        common_grid = np.arange(new_min, new_max + delta, delta)
        
        # 防止空网格
        if len(common_grid) < 2:
            common_grid = np.linspace(new_min, new_max, self.L)
            delta = common_grid[1] - common_grid[0]

        # 3. 把两条 PDF 插值到公共网格
        pdf1_rs = np.interp(common_grid, grid1, pdf1, left=0, right=0)
        pdf2_rs = np.interp(common_grid, grid2, pdf2, left=0, right=0)

        # 4. FFT 卷积
        conv = signal.fftconvolve(pdf1_rs, pdf2_rs, mode='full') * delta

        # 5. 构造卷积后的网格
        conv_len = len(conv)
        if conv_len == 0:
            # 如果卷积失败，返回均匀分布
            return np.ones(self.L) / self.L, new_grid
        
        conv_grid = np.linspace(grid1[0] + grid2[0],
                                grid1[-1] + grid2[-1],
                                conv_len)

        # 6. 重采样到最终长度
        if len(conv_grid) < 2:
            # 如果网格太小，返回均匀分布
            return np.ones(self.L) / self.L, new_grid
        
        result = self._resample_pdf(conv, conv_grid, new_grid)
        return result, new_grid

    
    # original version
    def _convolve_pdfs_0(self, pdf1, grid1, pdf2, grid2):
        """卷积两个PDF"""
        # 创建新的网格
        new_min = grid1[0] + grid2[0]
        new_max = grid1[-1] + grid2[-1]
        new_grid = np.linspace(new_min, new_max, self.L)
        
        # 使用FFT卷积（更高效）
        # 但需要确保网格均匀
        delta1 = grid1[1] - grid1[0]
        delta2 = grid2[1] - grid2[0]
        
        if abs(delta1 - delta2) < 1e-6:  # 网格间距相同
            # conv = signal.fftconvolve(pdf1, pdf2, mode='same') * delta1
            # conv_grid = grid1 + np.mean(grid2)
            # # 重采样到新网格
            # result = self._resample_pdf(conv, conv_grid, new_grid)

            conv = signal.fftconvolve(pdf1, pdf2, mode='full') * delta1

            # 计算对应网格
            conv_grid = np.linspace(
                grid1[0] + grid2[0],
                grid1[-1] + grid2[-1],
                len(conv)
            )

            # 再重采样到固定长度
            result = self._resample_pdf(conv, conv_grid, new_grid)

        else:
            # 直接数值卷积（较慢但更准确）
            result = np.zeros(len(new_grid))
            for i, x in enumerate(new_grid):
                # 计算 P(X1 + X2 = x)
                for j, x1 in enumerate(grid1):
                    x2 = x - x1
                    # 在grid2上插值
                    p2 = np.interp(x2, grid2, pdf2, left=0, right=0)
                    result[i] += pdf1[j] * p2 * delta1
        
        return result, new_grid
    
    def decode(self, y, max_iterations=30, verbose=True):
        """
        LDLC迭代解码算法
        """
        # 初始化：每个变量节点的消息是以观测值为中心的高斯
        var_to_check_msgs = {}
        var_to_check_grids = {}
        
        for var_node in range(self.n):
            grid = self._create_pdf_grid(y[var_node], self.pdf_range)
            pdf = self._gaussian_pdf(grid, y[var_node], self.sigma2)
            
            for check_node in self.var_to_check[var_node]:
                var_to_check_msgs[(var_node, check_node)] = pdf.copy()
                var_to_check_grids[(var_node, check_node)] = grid.copy()
        
        # 迭代解码
        for iteration in range(max_iterations):
            # if verbose and iteration % 5 == 0:
            #     print(f"迭代 {iteration}...")
            
            # === 校验节点更新 ===
            check_to_var_msgs = {}
            check_to_var_grids = {}
            
            for check_node in range(self.n):
                var_nodes = self.check_to_var[check_node]
                
                if len(var_nodes) < 2:
                    continue
                
                for j, target_var in enumerate(var_nodes):
                    h_j = self.edges[(target_var, check_node)]
                    
                    # 收集其他变量的消息并卷积
                    conv_pdf = None
                    conv_grid = None
                    
                    for k, other_var in enumerate(var_nodes):
                        if k == j:
                            continue
                        
                        h_k = self.edges[(other_var, check_node)]
                        if abs(h_k) < 1e-10:
                            continue
                        msg = var_to_check_msgs[(other_var, check_node)]
                        grid = var_to_check_grids[(other_var, check_node)]
                        
                        # 缩放：f(x) -> f(x/h_k) 等价于网格缩放
                        scaled_grid = grid * h_k
                        
                        if conv_pdf is None:
                            conv_pdf = msg
                            conv_grid = scaled_grid
                        else:
                            # 卷积
                            conv_pdf, conv_grid = self._convolve_pdfs(
                                conv_pdf, conv_grid, msg, scaled_grid
                            )
                    
                    if conv_pdf is None:
                        # 如果没有其他变量，使用均匀分布
                        conv_grid = self._create_pdf_grid(0, self.pdf_range)
                        conv_pdf = np.ones(len(conv_grid)) / len(conv_grid)
                    
                    output_grid = conv_grid / (-h_j)
                    stretched_pdf = np.abs(1.0 / h_j) * conv_pdf
                    # output_grid = -conv_grid * h_j
                    # stretched_pdf = np.abs(1.0 / h_j) * conv_pdf
                    
                    # 周期扩展：添加所有可能的整数偏移
                    period = 1.0 / abs(h_j)
                    extended_grid = self._create_pdf_grid(np.mean(output_grid), self.pdf_range)
                    extended_pdf = np.zeros(len(extended_grid))
                    
                    # 对于每个可能的整数偏移
                    num_periods = int(self.pdf_range / period) + 2
                    for i in range(-num_periods, num_periods + 1):
                        shifted_grid = output_grid + i * period
                        # shifted_pdf = self._resample_pdf(conv_pdf, shifted_grid, extended_grid)
                        shifted_pdf = self._resample_pdf(stretched_pdf, shifted_grid, extended_grid)
                        extended_pdf += shifted_pdf
                    
                    # 归一化
                    total = np.sum(extended_pdf) * self.delta
                    if total > 1e-10:
                        extended_pdf /= total
                    
                    check_to_var_msgs[(target_var, check_node)] = extended_pdf
                    check_to_var_grids[(target_var, check_node)] = extended_grid
            
            # === 变量节点更新 ===
            var_to_check_msgs_new = {}
            var_to_check_grids_new = {}
            
            for var_node in range(self.n):
                check_nodes = self.var_to_check[var_node]
                
                if len(check_nodes) == 0:
                    continue
                
                # 创建以观测值为中心的网格
                center_grid = self._create_pdf_grid(y[var_node], self.pdf_range)
                channel_pdf = self._gaussian_pdf(center_grid, y[var_node], self.sigma2)
                
                for j, target_check in enumerate(check_nodes):
                    # 乘积：信道PDF × 其他校验节点的消息
                    product_pdf = channel_pdf.copy()
                    product_grid = center_grid.copy()
                    
                    for k, other_check in enumerate(check_nodes):
                        if k == j:
                            continue
                        
                        if (var_node, other_check) in check_to_var_msgs:
                            msg = check_to_var_msgs[(var_node, other_check)]
                            msg_grid = check_to_var_grids[(var_node, other_check)]
                            
                            # 重采样到当前网格
                            resampled_msg = self._resample_pdf(msg, msg_grid, product_grid)
                            product_pdf *= resampled_msg
                    
                    # 归一化
                    total = np.sum(product_pdf) * self.delta
                    if total > 1e-10:
                        product_pdf /= total
                    
                    var_to_check_msgs_new[(var_node, target_check)] = product_pdf
                    var_to_check_grids_new[(var_node, target_check)] = product_grid
            
            var_to_check_msgs = var_to_check_msgs_new
            var_to_check_grids = var_to_check_grids_new
        
        # === 最终决策 ===
        x_hat = np.zeros(self.n)
        
        for var_node in range(self.n):
            # 组合所有校验节点的消息
            grid = self._create_pdf_grid(y[var_node], self.pdf_range)
            final_pdf = self._gaussian_pdf(grid, y[var_node], self.sigma2)
            
            for check_node in self.var_to_check[var_node]:
                if (var_node, check_node) in check_to_var_msgs:
                    msg = check_to_var_msgs[(var_node, check_node)]
                    msg_grid = check_to_var_grids[(var_node, check_node)]
                    resampled = self._resample_pdf(msg, msg_grid, grid)
                    final_pdf *= resampled
            
            # 找峰值
            if np.sum(final_pdf) > 1e-10:
                peak_idx = np.argmax(final_pdf)
                x_hat[var_node] = grid[peak_idx]
            else:
                # 如果PDF全是0，使用观测值
                x_hat[var_node] = y[var_node]
            
            if verbose:
                print(f"变量 {var_node}: y={y[var_node]:.2f}, x_hat={x_hat[var_node]:.2f}, 峰值={np.max(final_pdf):.2e}")
        
        # 估计整数信息向量
        # b_hat = np.round(self.H @ x_hat).astype(int)
        b_hat = np.rint(self.H @ x_hat).astype(int)
        
        return b_hat, x_hat


# === 使用示例 ===
if __name__ == "__main__":
    matrix_file_name = 'H_G_demo_8_dimension.npz'
    n = 8
    # matrix_file_name = 'H_G_demo_8_dimension.npz'

    matrix_data = np.load(matrix_file_name)
    H_norm = matrix_data['H']
    G_norm = matrix_data['G']

    print("H @ G =", np.round(H_norm @ G_norm, 4))

    
    # 创建简单的信息向量
    b = np.array([0, 0, 0, 0, 0, 0, 0, 0])
    print(f"\n信息向量 b: {b}")
    
    # 编码
    x = G_norm @ b
    print(f"码字 x: {np.round(x, 4)}")
    print(f"||x|| = {np.linalg.norm(x):.4f}")
    
    # 验证编码正确性
    Hx = H_norm @ x
    print(f"H @ x (应该≈b): {np.round(Hx, 4)}")
    
    # 添加噪声
    sigma2 = 1 / (2.0 * np.pi * np.e)
    # sigma2 = sigma2 * 0.9
    np.random.seed(42)
    noise = np.random.normal(0, np.sqrt(sigma2), n)
    y = x + noise
    
    print(f"\n噪声方差: σ² = {sigma2}")
    print(f"噪声码字 y: {np.round(y, 4)}")
    print(f"SNR: {10*np.log10(np.linalg.norm(x)**2 / np.linalg.norm(noise)**2):.2f} dB")
    
    # 解码
    print("\n" + "="*60)
    print("开始解码...")
    print("="*60)

    print(H_norm)
    
    decoder = LDLCDecoder(H_norm, sigma2, resolution=1/16, pdf_range=15.0)

    # exit()

    b_hat, x_hat = decoder.decode(y, max_iterations=1000, verbose=False)
    
    print("\n" + "="*60)
    print("解码结果:")
    print("="*60)
    print(f"估计的信息向量 b_hat: {b_hat}")
    print(f"实际信息向量 b:       {b}")
    print(f"\n估计的码字 x_hat: {np.round(x_hat, 4)}")
    print(f"实际码字 x:       {np.round(x, 4)}")
    
    print(f"\n误差分析:")
    print(f"  ||b - b_hat|| = {np.linalg.norm(b - b_hat):.6f}")
    print(f"  ||x - x_hat|| = {np.linalg.norm(x - x_hat):.6f}")
    print(f"  错误位数: {np.sum(b != b_hat)}/{n}")
    
    if np.allclose(b, b_hat):
        print("\n✓ 解码完全正确！")
    else:
        print(f"\n✗ 解码有误差")
        
        # 尝试线性解码作为对比
        print("\n使用线性解码器（H @ y）作为对比:")
        b_linear = np.round(H_norm @ y).astype(int)
        print(f"线性解码结果: {b_linear}")
        print(f"线性解码误差: {np.sum(b != b_linear)}/{n}")