#include <bits/stdc++.h>
using namespace std;

/**
 * Problem: Add Two Numbers
 * Complexity: O(T) time, O(1) space.
 * Constraints: 0 <= A, B <= 10000. 
 * Even though A and B fit in a standard int, using long long is a safe 
 * practice for competitive programming to prevent potential overflow 
 * in arithmetic operations.
 */

int main() {
    // Fast I/O setup
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t;
    if (!(cin >> t)) return 0;

    while (t--) {
        long long a, b;
        if (cin >> a >> b) {
            cout << (a + b) << "\n";
        }
    }

    return 0;
}