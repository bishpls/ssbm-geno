// Extra C API on top of blargg's snes_spc 0.9.0 (accurate DSP): DSP register and RAM access.
#include "SNES_SPC.h"
int spcx_dry = 0;
int spcx_nosat = 0;
extern "C" {
void spcx_set_nosat(int on) { spcx_nosat = on; }
void spcx_set_dry(SNES_SPC* s, int on) { spcx_dry = on; if (on) { s->dsp.write(0x2C, 0); s->dsp.write(0x3C, 0); } }
void spcx_dsp_write(SNES_SPC* s, int addr, int data) { s->dsp.write(addr, data); }
int  spcx_dsp_read(SNES_SPC* s, int addr) { return s->dsp.read(addr); }
int  spcx_ram_read(SNES_SPC* s, int addr) { return s->m.ram.ram[addr & 0xFFFF]; }
void spcx_ram_write(SNES_SPC* s, int addr, int data) { s->m.ram.ram[addr & 0xFFFF] = (uint8_t)data; }
int  spcx_pc(SNES_SPC* s) { return s->m.cpu_regs.pc; }
}
