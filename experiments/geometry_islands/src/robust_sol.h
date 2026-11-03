    void apply_cov(int o,const vector<Pt>&h){
        if(!g_geo_exact){legacy_apply_cov(o,h);return;}if(h.empty())return;
        double x0=1e300,x1=-1e300,y0=1e300,y1=-1e300;for(Pt p:h){x0=min(x0,p.x);x1=max(x1,p.x);y0=min(y0,p.y);y1=max(y1,p.y);}
        char*row=&incov[(size_t)o*np];for(int i:g_geo_grid.query(*I,x0,x1,y0,y1))if(geo_exact_covers(h,I->P[i])){row[i]=1;cov[i]++;covlist[o].push_back(i);}
    }
    bool geo_ok(int x,int o,vector<Pt>&newh)const{
        if(!g_geo_exact)return legacy_geo_ok(x,o,newh);newh.clear();const char*row=&incov[(size_t)o*np];if(row[x])return true;
        newh=hull[o];newh.push_back(I->P[x]);hull_of(newh);
        double x0=1e300,x1=-1e300,y0=1e300,y1=-1e300;for(Pt p:newh){x0=min(x0,p.x);x1=max(x1,p.x);y0=min(y0,p.y);y1=max(y1,p.y);}
        for(int i:g_geo_grid.query(*I,x0,x1,y0,y1))if(!row[i]&&cov[i]&&geo_exact_covers(newh,I->P[i]))return false;return true;
    }
