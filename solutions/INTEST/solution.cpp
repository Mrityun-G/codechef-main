#include <bits/stdc++.h>
using namespace std;

/**
 * Problem: Enormous Input Test (INTEST)
 * The problem requires reading up to 10^7 integers and checking divisibility by K.
 * Given the large input size (10^7), fast I/O is mandatory to stay within the 8s time limit.
 * Using ios_base::sync_with_stdio(false) and cin.tie(NULL) is sufficient for this constraint.
 */

int main() {
    // Optimize standard I/O operations for speed
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n;
    long long k;
    
    // Read N and K
    if (!(cin >> n >> k)) return 0;

    int count = 0;
    long long a;

    // Process each of the N integers
    for (int i = 0; i < n; ++i) {
        cin >> a;
        // Check divisibility
        if (a % k == 0) {
            count++;
        }
    }

    // Output the final count
    cout << count << "\n";

    return 0;
}