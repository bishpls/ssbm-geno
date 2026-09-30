import sys, numpy as np, soundfile as sf, librosa, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
def sheet(paths, out, fmax=12000, cols=1):
    n=len(paths); fig,axs=plt.subplots(n,1,figsize=(16,2.4*n)); axs=np.atleast_1d(axs)
    for ax,p in zip(axs,paths):
        x,sr=sf.read(p); x=x.mean(1) if x.ndim>1 else x
        S=librosa.stft(x,n_fft=1024,hop_length=int(sr*0.004),win_length=int(sr*0.012)); D=20*np.log10(np.abs(S)+1e-7)
        f=np.linspace(0,sr/2,D.shape[0]); k=f<=fmax
        ax.imshow(D[k],origin='lower',aspect='auto',extent=[0,len(x)/sr,0,fmax/1000],cmap='magma',vmin=D.max()-70,vmax=D.max())
        env=np.array([np.sqrt(np.mean(x[i:i+int(sr*0.005)]**2)+1e-12) for i in range(0,len(x),int(sr*0.005))])
        a2=ax.twinx(); a2.plot(np.arange(len(env))*0.005, 20*np.log10(env),'c',lw=0.7); a2.set_ylim(-70,0)
        ax.set_title(p.split('/')[-1],fontsize=9); L=len(x)/sr
        ax.set_xticks(np.arange(0,L,0.05)); ax.tick_params(labelsize=7); ax.grid(alpha=0.25)
    plt.tight_layout(); plt.savefig(out,dpi=60); plt.close()
if __name__=='__main__': sheet(sys.argv[2:], sys.argv[1])
