// json.h: минимальный разбор JSON.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ===================================================================== JSON
// Специализированный парсер под известную схему: не строит дерево.
struct JReader {
    const char* p;
    const char* e;
    JReader(const char* b, const char* en) : p(b), e(en) {}
    void ws() { while (p < e && (unsigned char)*p <= ' ') p++; }
    bool eat(char c) { ws(); if (p < e && *p == c) { p++; return true; } return false; }
    void need(char c) { if (!eat(c)) throw runtime_error(string("expected ") + c); }
    double num() {
        ws();
        char* q;
        double v = strtod(p, &q);
        if (q == p) throw runtime_error("bad number");
        p = q;
        return v;
    }
    string str() {
        ws();
        need('"');
        string r;
        while (p < e && *p != '"') {
            if (*p == '\\') {
                p++;
                char c = *p++;
                switch (c) {
                    case 'n': r += '\n'; break;
                    case 't': r += '\t'; break;
                    case 'r': r += '\r'; break;
                    case 'b': r += '\b'; break;
                    case 'f': r += '\f'; break;
                    case 'u': p += 4; r += '?'; break;
                    default: r += c;
                }
            } else r += *p++;
        }
        need('"');
        return r;
    }
    void skip() {  // пропустить произвольное значение
        ws();
        if (p >= e) return;
        if (*p == '"') { str(); return; }
        if (*p == '{' || *p == '[') {
            char open = *p, close = open == '{' ? '}' : ']';
            int d = 0;
            bool instr = false;
            while (p < e) {
                char c = *p;
                if (instr) {
                    if (c == '\\') p++;
                    else if (c == '"') instr = false;
                } else if (c == '"') instr = true;
                else if (c == open) d++;
                else if (c == close) { d--; if (!d) { p++; return; } }
                p++;
            }
            return;
        }
        while (p < e && *p != ',' && *p != '}' && *p != ']') p++;
    }
};
