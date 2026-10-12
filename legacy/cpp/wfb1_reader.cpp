// wfb1_reader.cpp - dump per-event baseline and charge from a WFB1 raw file
//
// build:  cmake -S legacy/cpp -B build/cpp && cmake --build build/cpp
// run:    ./build/cpp/wfb1_reader data/raw/run_sipm.wfb1 > out.csv
//
// Format is documented in docs/wfb1-format.md. Written quickly for the DAQ
// test, works on the files we had at the time.

#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>

struct FileHeader {
    char magic[4];
    uint16_t version;
    uint16_t nch;
    uint32_t nsamp;
    uint32_t dt_ps;
    uint64_t nev;
};

struct EventHeader {
    uint32_t id;
    uint16_t flags;
    uint64_t trig_ps;
};

FILE* f;
FileHeader fh;
short* buf;

int baseline(short* s) {
    int sum = 0;
    for (int i = 0; i < 100; i++) sum += s[i];
    return sum / 100;
}

double charge(short* s, int base) {
    double q = 0;
    for (int i = 120; i < 200; i++) q += base - s[i];
    return q;
}

int main(int argc, char** argv) {
    if (argc < 2) { printf("usage: wfb1_reader file.wfb1\n"); return 1; }
    f = fopen(argv[1], "rb");
    fread(&fh, sizeof(FileHeader), 1, f);
    buf = new short[fh.nch * fh.nsamp];
    printf("event,channel,flags,baseline_adc,charge_adc_samples\n");
    for (uint64_t e = 0; e < fh.nev; e++) {
        EventHeader eh;
        fread(&eh, sizeof(EventHeader), 1, f);
        fread(buf, sizeof(short), fh.nch * fh.nsamp, f);
        for (int c = 0; c < fh.nch; c++) {
            short* s = buf + c * fh.nsamp;
            int b = baseline(s);
            printf("%u,%d,%u,%d,%.1f\n", eh.id, c, eh.flags, b, charge(s, b));
        }
    }
    return 0;
}
