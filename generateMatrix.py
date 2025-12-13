import numpy as np

# this file provide functions to generate corresponding H and G
# generate_magic_ldlc_H -> normalize_ldlc_H -> generate_G_from_H

def generate_magic_ldlc_H(n, d, h_values, seed=42):
    np.random.seed(seed)
    # Step 1: Initialize d random permutations of {0, ..., n-1}
    P = np.zeros((d, n), dtype=int)
    for i in range(d):
        P[i] = np.random.permutation(n)
    print("Random permutations P:")
    print(P)

    # Step 2: loop removal
    c = 0  # column index
    loopless_columns = 0
    while loopless_columns < n:
        changed_permutation = -1

        # Check for 2-loop
        for i in range(d):
            for j in range(i+1, d):
                if P[i, c] == P[j, c]:
                    changed_permutation = i
                    # print(f"2-loop found in column {c} between permutations {i} and {j}.")
                    break
            if changed_permutation != -1:
                break

        if changed_permutation == -1:
            # Check for 4-loop
            for c0 in range(n):
                if c0 == c:
                    continue
                col_c = set(P[:, c])
                col_c0 = set(P[:, c0])
                common = col_c & col_c0
                if len(common) >= 2:
                    for i in range(d):
                        if P[i, c] in common:
                            changed_permutation = i
                            # print("4-loop found in columns", c, "and", c0, "in permutation", i)
                            break
                    break

        if changed_permutation != -1:
            # Swap a random entry with column c
            # i = np.random.randint(n)
            i = np.random.randint(0, n-1)
            if i >= c:
                i += 1
            # Swap column c with column i in the selected permutation
            P[changed_permutation, c], P[changed_permutation, i] = P[changed_permutation, i], P[changed_permutation, c]
            loopless_columns = 0
            # print("after loop removal:")
            # print(P, '\n')
        else:
            loopless_columns += 1

        c += 1
        if c >= n:
            c = 0
    print("after loop removal:")
    print(P)

    # Step 3: Build H
    H = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(d):
            row = P[j, i]
            sign = np.random.choice([-1, 1])
            H[row, i] = h_values[j] * sign

    return H


def generate_G_from_H(H):
    I = np.eye(H.shape[0])
    G = np.linalg.solve(H, I)
    return G


def normalize_ldlc_H(H):
    det_H = np.linalg.det(H)
    if det_H == 0:
        raise ValueError("H is singular and not invertible.")
    scale = abs(det_H) ** (1.0 / H.shape[0])
    H_normalized = H / scale
    return H_normalized


if __name__ == "__main__":

    # is_save = False
    # matrix_file_name = 'H_G_demo_7_dimension.npz'

    # n = 7  # Example value for n
    # d = 3  # Example value for d
    # h_values = [0.5, 0.8, 1]  # Example values for h
    # seed = 42  # Random seed for reproducibility

    is_save = True
    # matrix_file_name = 'H_G_demo_8_dimension.npz'
    matrix_file_name = 'H_G_demo_32_dimension.npz'

    # n = 8  # Example value for n
    n = 32  # Example value for n
    d = 3  # Example value for d
    h_values = [0.5, 0.8, 1]  # Example values for h
    seed = 42  # Random seed for reproducibility

    # generate_magic_ldlc_H(n, d, h_values, seed)
    H = generate_magic_ldlc_H(n, d, h_values, seed)
    print("Generated matrix H:")
    print(H)

    H_norm = normalize_ldlc_H(H)
    assert np.allclose(abs(np.linalg.det(H_norm)), 1.0, atol=1e-8)
    print("Normalized matrix H:")
    print(H_norm)
    print("Determinant of H:", np.linalg.det(H_norm))

    # G = generate_G_from_H(H)
    # print("Generated matrix G:")
    # print(G)
    # print("Determinant of G:", np.linalg.det(G))

    G_norm = np.linalg.inv(H_norm)
    assert np.allclose(abs(np.linalg.det(G_norm)), 1.0, atol=1e-8)
    print("Normalized matrix G:")
    print(G_norm)
    print("Determinant of G:", np.linalg.det(G_norm))

    assert np.allclose(H_norm @ G_norm, np.eye(H.shape[0]), atol=1e-8)
    print("H_norm @ G_norm is close to identity matrix.")

    if is_save:
        np.savez(matrix_file_name, H=H_norm, G=G_norm)
        print("Matrices saved to .", matrix_file_name)



    