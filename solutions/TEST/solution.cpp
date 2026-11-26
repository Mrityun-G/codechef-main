#include <bits/stdc++.h>
using namespace std;

/**
 * Problem: Life, the Universe, and Everything
 * Approach: Read integers one by one from standard input.
 * If the integer is 42, terminate the program.
 * Otherwise, print the integer.
 * Time Complexity: O(N) where N is the number of inputs processed.
 * Space Complexity: O(1) as we only store the current integer.
 */

int main() {
    // Optimize I/O operations
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    long long n;
    // Read integers until EOF or until 42 is encountered
    while (cin >> n) {
        if (n == 42) {
            break;
        }
        cout << n << "\n";
    }

    return 0;
}