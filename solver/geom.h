// geom.h: точки, векторное произведение, выпуклая оболочка.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ================================================================ геометрия
struct Pt { double x = 0, y = 0; };
static inline bool ptless(const Pt& a, const Pt& b) { return a.x < b.x || (a.x == b.x && a.y < b.y); }
static inline bool pteq(const Pt& a, const Pt& b) { return a.x == b.x && a.y == b.y; }
static inline double cr(const Pt& o, const Pt& a, const Pt& b) {
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
}

// Выпуклая оболочка (монотонная цепь), CCW, без коллинеарных. 1, 2 или >=3 точки.
static void hull_of(vector<Pt>& p) {
    sort(p.begin(), p.end(), ptless);
    p.erase(unique(p.begin(), p.end(), pteq), p.end());
    size_t n = p.size();
    if (n <= 2) return;
    vector<Pt> h(2 * n);
    size_t k = 0;
    for (size_t i = 0; i < n; i++) {
        while (k >= 2 && cr(h[k - 2], h[k - 1], p[i]) <= 0) k--;
        h[k++] = p[i];
    }
    for (size_t i = n - 1, t = k + 1; i-- > 0;) {
        while (k >= t && cr(h[k - 2], h[k - 1], p[i]) <= 0) k--;
        h[k++] = p[i];
    }
    h.resize(k - 1);
    p.swap(h);
}
