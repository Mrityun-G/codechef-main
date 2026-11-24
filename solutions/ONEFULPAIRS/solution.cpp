#include <bits/stdc++.h>
using namespace std;

/**
 * Problem Analysis:
 * We are given two positive integers a and b.
 * We need to check if a + b + (a * b) == 111.
 * 
 * Constraints: 1 <= a, b <= 1000.
 * The maximum value of a + b + (a * b) would be 1000 + 1000 + (1000 * 1000) = 1,002,000.
 * This fits comfortably within a standard 32-bit signed integer (int), 
 * but using long long is safer practice in competitive programming to avoid overflow.
 */

int main() {
    // Fast I/O setup
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    long long a, b;
    if (!(cin >> a >> b)) return 0;

    // Calculate the expression
    long long result = a + b + (a * b);

    // Check if it equals 111
    if (result == 111) {
        cout << "Yes" << "\n";
    } else {
        cout << "No" << "\n";
    }

    return 0;
}