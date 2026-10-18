// inst.h: Inst: чтение инстанса, расстояния, навыки, рабочие.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// =================================================================== инстанс
struct Inst {
    int ns = 0, no = 0, nw = 0, nsk = 0;
    long long A = 0;
    double alpha = 0;
    vector<double> reward, cost;
    vector<int> ntask;                 // число задач сайта (с повторами)
    vector<int> maxsize;
    vector<vector<int>> skillset;      // уникальные навыки сайта
    vector<vector<int>> wskills;       // навыки рабочего
    vector<vector<char>> wmask;        // рабочий -> маска навыков
    vector<int> wcount;
    vector<int> Nk;                    // число рабочих с навыком k
    vector<double> D;                  // [o*ns + s]
    vector<double> prof;               // reward[s] - D[o][s]
    vector<char> servable;
    vector<Pt> P;                      // сайты, затем офисы
    vector<vector<int>> cand;          // сайт -> офисы по возрастанию расстояния
    bool simple_workers = true;        // у каждого рабочего ровно один навык
    double ext = 1, eps_len = 0, eps_cr = 0;
    int totalTasks = 0;

    // равномерная сетка по всем точкам P: запросы «точки в прямоугольнике» без прохода по всем
    int gnx = 1, gny = 1;
    double gx0 = 0, gy0 = 0, gcw = 1, gch = 1;
    vector<int> gstart, gpts;          // точки ячейки c: gpts[gstart[c] .. gstart[c+1])

    void build_grid() {
        int n = P.size();
        if (n == 0) { gstart.assign(2, 0); return; }
        double mnx = 1e300, mxx = -1e300, mny = 1e300, mxy = -1e300;
        for (auto& q : P) { mnx = min(mnx, q.x); mxx = max(mxx, q.x); mny = min(mny, q.y); mxy = max(mxy, q.y); }
        int g = max(1, (int)sqrt(n / 2.0));
        gnx = gny = g;
        gx0 = mnx; gy0 = mny;
        gcw = (mxx - mnx) / g; gch = (mxy - mny) / g;
        if (!(gcw > 0)) { gcw = 1; gnx = 1; }
        if (!(gch > 0)) { gch = 1; gny = 1; }
        vector<int> cell(n);
        gstart.assign((size_t)gnx * gny + 1, 0);
        for (int i = 0; i < n; i++) {
            int cx = min(gnx - 1, max(0, (int)((P[i].x - gx0) / gcw)));
            int cy = min(gny - 1, max(0, (int)((P[i].y - gy0) / gch)));
            cell[i] = cy * gnx + cx;
            gstart[cell[i] + 1]++;
        }
        for (size_t c = 1; c < gstart.size(); c++) gstart[c] += gstart[c - 1];
        gpts.resize(n);
        vector<int> fillp(gstart.begin(), gstart.end() - 1);
        for (int i = 0; i < n; i++) gpts[fillp[cell[i]]++] = i;
    }
    // f(i) для каждой точки, чья ячейка пересекает [x0,x1]×[y0,y1] (надмножество точек прямоугольника)
    template <class F> void for_box(double x0, double x1, double y0, double y1, F&& f) const {
        if (!(x1 >= x0) || !(y1 >= y0)) return;
        auto ci = [](double v, int g) { return v < 0 ? 0 : v >= g ? g - 1 : (int)v; };
        int cx0 = ci(floor((x0 - gx0) / gcw), gnx), cx1 = ci(floor((x1 - gx0) / gcw), gnx);
        int cy0 = ci(floor((y0 - gy0) / gch), gny), cy1 = ci(floor((y1 - gy0) / gch), gny);
        for (int cy = cy0; cy <= cy1; cy++) {
            int c0 = cy * gnx;
            for (int i = gstart[c0 + cx0]; i < gstart[c0 + cx1 + 1]; i++) f(gpts[i]);
        }
    }

    inline double d(int o, int s) const { return D[(size_t)o * ns + s]; }
    inline double pr(int o, int s) const { return prof[(size_t)o * ns + s]; }
};

static Inst load_instance(const string& path) {
    ifstream f(path, ios::binary);
    if (!f) throw runtime_error("no input file");
    string src((istreambuf_iterator<char>(f)), istreambuf_iterator<char>());
    size_t off = 0;
    if (src.size() >= 3 && (unsigned char)src[0] == 0xEF) off = 3;
    JReader R(src.data() + off, src.data() + src.size());
    Inst I;
    vector<vector<int>> tasks;
    vector<double> flatD;
    vector<Pt> sitePts, offPts;
    bool haveA = false, haveAl = false;
    R.need('{');
    if (!R.eat('}')) {
        while (true) {
            string key = R.str();
            R.need(':');
            if (key == "sites") {
                R.need('[');
                if (!R.eat(']')) while (true) {
                    R.need('{');
                    Pt q; double rw = 0; vector<int> tk;
                    if (!R.eat('}')) while (true) {
                        string k2 = R.str(); R.need(':');
                        if (k2 == "x") q.x = R.num();
                        else if (k2 == "y") q.y = R.num();
                        else if (k2 == "reward") rw = R.num();
                        else if (k2 == "tasks") {
                            R.need('[');
                            if (!R.eat(']')) while (true) { tk.push_back((int)llround(R.num())); if (R.eat(',')) continue; R.need(']'); break; }
                        } else R.skip();
                        if (R.eat(',')) continue;
                        R.need('}'); break;
                    }
                    sitePts.push_back(q); I.reward.push_back(rw); tasks.push_back(move(tk));
                    if (R.eat(',')) continue;
                    R.need(']'); break;
                }
            } else if (key == "offices") {
                R.need('[');
                if (!R.eat(']')) while (true) {
                    R.need('{');
                    Pt q; double c = 0; long long ms = 0;
                    if (!R.eat('}')) while (true) {
                        string k2 = R.str(); R.need(':');
                        if (k2 == "x") q.x = R.num();
                        else if (k2 == "y") q.y = R.num();
                        else if (k2 == "cost") c = R.num();
                        else if (k2 == "maxSize") ms = (long long)llround(R.num());
                        else R.skip();
                        if (R.eat(',')) continue;
                        R.need('}'); break;
                    }
                    I.cost.push_back(c);
                    I.maxsize.push_back((int)max(0LL, min(ms, (long long)INT_MAX)));
                    offPts.push_back(q);
                    if (R.eat(',')) continue;
                    R.need(']'); break;
                }
            } else if (key == "workers") {
                R.need('[');
                if (!R.eat(']')) while (true) {
                    vector<int> sk;
                    R.need('[');
                    if (!R.eat(']')) while (true) { sk.push_back((int)llround(R.num())); if (R.eat(',')) continue; R.need(']'); break; }
                    I.wskills.push_back(move(sk));
                    if (R.eat(',')) continue;
                    R.need(']'); break;
                }
            } else if (key == "distances") {
                R.need('[');
                if (!R.eat(']')) while (true) {
                    R.need('[');
                    if (!R.eat(']')) while (true) { flatD.push_back(R.num()); if (R.eat(',')) continue; R.need(']'); break; }
                    if (R.eat(',')) continue;
                    R.need(']'); break;
                }
            } else if (key == "maxDifference") { I.A = (long long)llround(R.num()); haveA = true; }
            else if (key == "balanceCoefficient") { I.alpha = R.num(); haveAl = true; }
            else R.skip();
            if (R.eat(',')) continue;
            R.need('}'); break;
        }
    }
    I.ns = tasks.size();
    I.no = I.cost.size();
    I.nw = I.wskills.size();
    if (!haveA) I.A = I.ns;
    if (!haveAl) I.alpha = 0;
    if (I.A < 0) I.A = 0;
    I.P.clear();
    I.P.reserve(I.ns + I.no);
    I.P.insert(I.P.end(), sitePts.begin(), sitePts.end());
    I.P.insert(I.P.end(), offPts.begin(), offPts.end());
    int maxsk = 0;
    for (auto& t : tasks) for (int k : t) maxsk = max(maxsk, k + 1);
    for (auto& w : I.wskills) for (int k : w) maxsk = max(maxsk, k + 1);
    I.nsk = max(1, maxsk);
    I.ntask.resize(I.ns);
    I.skillset.resize(I.ns);
    for (int s = 0; s < I.ns; s++) {
        I.ntask[s] = tasks[s].size();
        I.totalTasks += I.ntask[s];
        set<int> u(tasks[s].begin(), tasks[s].end());
        I.skillset[s].assign(u.begin(), u.end());
    }
    I.Nk.assign(I.nsk, 0);
    I.wmask.assign(I.nw, vector<char>(I.nsk, 0));
    I.wcount.assign(I.nw, 0);
    for (int w = 0; w < I.nw; w++) {
        set<int> u(I.wskills[w].begin(), I.wskills[w].end());
        for (int k : u) { I.wmask[w][k] = 1; I.Nk[k]++; }
        I.wcount[w] = u.size();
        if ((int)u.size() != 1) I.simple_workers = false;
    }
    I.servable.assign(I.ns, 1);
    for (int s = 0; s < I.ns; s++)
        for (int k : I.skillset[s]) if (I.Nk[k] == 0) I.servable[s] = 0;
    // расстояния
    I.D.assign((size_t)I.no * I.ns, 0.0);
    if ((long long)flatD.size() == (long long)I.no * I.ns)
        copy(flatD.begin(), flatD.end(), I.D.begin());
    else if (!flatD.empty())
        for (size_t i = 0; i < min(flatD.size(), I.D.size()); i++) I.D[i] = flatD[i];
    I.prof.resize(I.D.size());
    for (int o = 0; o < I.no; o++)
        for (int s = 0; s < I.ns; s++) I.prof[(size_t)o * I.ns + s] = I.reward[s] - I.D[(size_t)o * I.ns + s];
    double mnx = 1e300, mxx = -1e300, mny = 1e300, mxy = -1e300;
    for (auto& q : I.P) { mnx = min(mnx, q.x); mxx = max(mxx, q.x); mny = min(mny, q.y); mxy = max(mxy, q.y); }
    I.ext = I.P.empty() ? 1.0 : max(mxx - mnx, mxy - mny);
    if (!(I.ext > 0)) I.ext = 1.0;
    I.eps_len = 1e-9 * I.ext;
    I.eps_cr = 1e-9 * I.ext * I.ext;
    I.build_grid();
    // кандидаты: офисы по возрастанию расстояния
    I.cand.resize(I.ns);
    {
        vector<int> all(I.no);
        iota(all.begin(), all.end(), 0);
        for (int s = 0; s < I.ns; s++) {
            vector<int> v = all;
            sort(v.begin(), v.end(), [&](int a, int b) { return I.d(a, s) < I.d(b, s); });
            I.cand[s] = move(v);
        }
    }
    return I;
}
