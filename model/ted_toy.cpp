// ted_toy.cpp - float golden model of the toy MM CDR loop (OSR = 2).
// usage: ted_cpp <stim.txt> <out_tau.txt> <n_sym> <kp_shift> <ki_shift> <tau0_samples>
// Output: one line per symbol = tau in SAMPLES, wrapped to [0, 2).
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 7) { std::fprintf(stderr, "usage: see header\n"); return 1; }
    std::ifstream fin(argv[1]);
    std::vector<double> x; int v6;
    while (fin >> v6) x.push_back(double(v6) - 32.0);   // unsigned 6-bit -> centered
    const int    n_sym = std::atoi(argv[3]);
    const double kp    = std::ldexp(1.0, -std::atoi(argv[4]));
    const double ki    = std::ldexp(1.0, -std::atoi(argv[5]));
    double tau = std::atof(argv[6]);                      // samples, in [0,2)
    double v = 0.0, y_prev = 0.0, a_prev = 1.0;

    std::FILE* fo = std::fopen(argv[2], "w");
    for (int k = 0; k < n_sym; ++k) {
        std::fprintf(fo, "%.9f\n", tau);
        const int    ip = int(std::floor(tau));
        const double mu = tau - ip;
        const int    n  = 2 * k + ip;                     // NCO base pointer
        if (n + 1 >= int(x.size())) break;
        const double y = x[n] + mu * (x[n + 1] - x[n]);   // linear interpolator
        const double a = (y >= 0.0) ? 1.0 : -1.0;         // decision
        const double e = (k == 0) ? 0.0 : a_prev * y - a * y_prev;   // MM TED
        v   += ki * e;                                    // PI integrator
        tau += kp * e + v;                                // NCO
        while (tau >= 2.0) tau -= 2.0;                    // wrap = 1 UI slip
        while (tau <  0.0) tau += 2.0;
        y_prev = y; a_prev = a;
    }
    std::fclose(fo);
    return 0;
}
