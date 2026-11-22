#include <bits/stdc++.h>
using namespace std;

/**
 * Problem Analysis:
 * The problem states that for each language, there are 2 courses.
 * If there are N languages, the total number of courses is 2 * N.
 * Constraints: 1 <= N <= 100.
 * Time Complexity: O(1) per test case.
 * Space Complexity: O(1).
 */

int main() {
    // Fast I/O setup
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // The problem description implies a single integer input N.
    // While the prompt mentions handling multiple test cases, the specific 
    // problem description for CCLEARN only provides a single integer N.
    // We will read N and output 2 * N.
    
    long long n;
    if (cin >> n) {
        cout << (n * 2) << "\n";
    }

    return 0;
}