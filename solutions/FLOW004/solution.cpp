#include <bits/stdc++.h>
using namespace std;

/**
 * Problem: First and Last Digit (FLOW004)
 * Approach:
 * 1. Read the number as a string to easily access the first and last characters.
 * 2. The last digit is the character at index (length - 1).
 * 3. The first digit is the character at index 0.
 * 4. Convert these characters to their integer values by subtracting '0'.
 * 5. Sum them and print the result.
 * 
 * Time Complexity: O(D) per test case, where D is the number of digits (max 7).
 * Space Complexity: O(D) to store the string representation of the number.
 */

int main() {
    // Fast I/O for competitive programming
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t;
    if (!(cin >> t)) return 0;

    while (t--) {
        string n;
        cin >> n;

        if (n.empty()) continue;

        // First digit is at index 0
        int first_digit = n.front() - '0';
        // Last digit is at index length - 1
        int last_digit = n.back() - '0';

        cout << (first_digit + last_digit) << "\n";
    }

    return 0;
}