#include <bits/stdc++.h>
using namespace std;

/**
 * Problem: FCTRL2 - Small factorials
 * The factorial of 100 is a very large number (158 digits), 
 * which exceeds the capacity of standard 64-bit integers.
 * We must use an array-based approach to perform arbitrary-precision multiplication.
 */

void solve() {
    int n;
    cin >> n;

    if (n == 0 || n == 1) {
        cout << 1 << "\n";
        return;
    }

    // Array to store digits of the factorial. 
    // 100! has 158 digits, so 200 is safe.
    vector<int> res;
    res.push_back(1);

    for (int i = 2; i <= n; ++i) {
        int carry = 0;
        for (int j = 0; j < res.size(); ++j) {
            int prod = res[j] * i + carry;
            res[j] = prod % 10;
            carry = prod / 10;
        }
        while (carry) {
            res.push_back(carry % 10);
            carry /= 10;
        }
    }

    // Print digits in reverse order
    for (int i = res.size() - 1; i >= 0; --i) {
        cout << res[i];
    }
    cout << "\n";
}

int main() {
    // Fast I/O
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t;
    if (!(cin >> t)) return 0;
    while (t--) {
        solve();
    }
    return 0;
}