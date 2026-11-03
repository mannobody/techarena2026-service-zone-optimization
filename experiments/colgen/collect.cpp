// Offline observer of the unmodified solver. Not the contest column-generation
// executable. Prints a pool of zones from best/elite states to stdout, while the
// included solver reads its input and writes its ordinary solution as usual.
// It never reads a cache or writes an extra runtime file.
#define main colgen_baseline_main
#include "../../solver/solve.cpp"
#undef main

int main(int argc, char** argv) {
    atomic<bool> done{false};
    set<pair<int, vector<int>>> zones;
    auto capture = [&](const vector<int>& asg, const vector<char>& op) {
        vector<vector<int>> mem(op.size());
        for (size_t i = 0; i < asg.size(); i++)
            if (asg[i] >= 0) mem[asg[i]].push_back((int)i);
        for (size_t o = 0; o < mem.size(); o++)
            if (!mem[o].empty()) zones.insert({(int)o, move(mem[o])});
    };
    auto sample = [&]() {
        {
            lock_guard<mutex> lk(g_best_mx);
            capture(g_best_asg, g_best_open);
        }
        {
            lock_guard<mutex> lk(g_el_mx);
            for (const auto& e : g_elite) capture(e.asg, e.open);
        }
    };
    thread observer([&]() {
        while (!done.load(memory_order_relaxed)) {
            sample();
            this_thread::sleep_for(chrono::milliseconds(5));
        }
    });
    int rc = colgen_baseline_main(argc, argv);
    done.store(true, memory_order_relaxed);
    observer.join();
    sample();
    printf("[");
    bool first = true;
    for (const auto& z : zones) {
        if (!first) printf(",");
        first = false;
        printf("{\"officeId\":%d,\"sites\":[", z.first);
        for (size_t i = 0; i < z.second.size(); i++) printf("%s%d", i ? "," : "", z.second[i]);
        printf("]}");
    }
    printf("]\n");
    return rc;
}
