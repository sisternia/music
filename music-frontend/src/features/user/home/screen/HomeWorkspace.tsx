'use dom';

import { useEffect, useRef, useState } from 'react';
import PianoKeyboard from '@/features/user/piano/screen/PianoKeyboard';
import PianoImport from '@/features/user/piano/screen/PianoImport';
import { configurePianoApi, pianoRequest, type PianoSong } from '@/features/user/piano/hooks/transcription';
import { PIANO_EDITION_ENABLED } from '@/features/user/piano/hooks/features';
import { pianoPublicAsset } from '@/features/user/piano/hooks/public-assets';
import { useHomeNoteAnimation } from '../hooks/useHomeNoteAnimation';
import AuthDialog from '@/features/auth/screen/AuthDialog';
import './workspace.css';

type Project = { id: string; title: string; duration: number; updated: string; favorite?: boolean };
export type WorkspaceView = 'new' | 'piano' | 'projects' | 'collections';
type Props = { apiUrl?: string; nativeHost?: boolean; initialView?: WorkspaceView; dom?: import('expo/dom').DOMProps };
const STORAGE = 'auralis.piano.projects.v1';
const logo = pianoPublicAsset('images/Logo Cursive Harmony Auralis.png');
const musicSymbols = ['♪', '♫', '♬', '♩', '♭', '♯', '♮', '𝄞', '♭', '♫', '♪', '♬', '♩', '♯', '♫', '𝄢', '♪', '♮', '♬', '♭', '♫', '♩'];
const viewRoutes: Record<WorkspaceView, string> = { new: '/new-transcription', piano: '/piano', projects: '/projects', collections: '/collections' };
const viewTitles: Record<WorkspaceView, string> = { new: 'New transcription', piano: 'Piano', projects: 'Projects', collections: 'Collections' };

function viewFromPath(pathname: string): WorkspaceView {
  if (pathname.startsWith('/piano')) return 'piano';
  if (pathname.startsWith('/projects')) return 'projects';
  if (pathname.startsWith('/collections')) return 'collections';
  return 'new';
}

function StudioMark({ small = false }: { small?: boolean }) {
  return <svg width={small ? 27 : 48} height={small ? 30 : 52} viewBox="0 0 48 52" fill="none" aria-hidden="true"><path d="M6 25v6M14 18v20M23 10v32M32 4v33M41 18v12" stroke="currentColor" strokeWidth="5" strokeLinecap="round" /><path d="m23 42 9-5" stroke="currentColor" strokeWidth="5" strokeLinecap="round" /></svg>;
}

export default function HomeWorkspace({ apiUrl, nativeHost = false, initialView = 'new' }: Props) {
  const [view, setView] = useState<WorkspaceView>(initialView);
  const [seed, setSeed] = useState<PianoSong | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [collapsed, setCollapsed] = useState(false);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [editNew, setEditNew] = useState(false);
  const [pianoSession, setPianoSession] = useState(0);
  const [authOpen, setAuthOpen] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  const homeStage = useRef<HTMLDivElement>(null);
  useHomeNoteAnimation(homeStage, view === 'new');
  const navigate = (next: WorkspaceView) => {
    setView(next);
    if (!nativeHost && typeof window !== 'undefined' && window.location.pathname !== viewRoutes[next]) {
      window.history.pushState({ workspaceView: next }, '', viewRoutes[next]);
    }
  };
  useEffect(() => {
    if (nativeHost || typeof window === 'undefined') return;
    document.title = `${seed?.title && view === 'piano' ? seed.title : viewTitles[view]} | Harmony Auralis`;
  }, [nativeHost, seed?.title, view]);
  useEffect(() => {
    if (nativeHost || typeof window === 'undefined') return;
    const onPopState = () => {
      const next = viewFromPath(window.location.pathname);
      setSeed(null);
      setEditNew(false);
      setView(next);
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, [nativeHost]);
  useEffect(() => {
    configurePianoApi(apiUrl);
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE) || '[]');
      if (Array.isArray(saved)) queueMicrotask(() => setProjects(saved.filter(item => typeof item.id === 'string' && typeof item.title === 'string')));
    } catch { /* Private browsing can disable local storage. */ }
  }, [apiUrl]);

  const remember = (song: PianoSong, previousId?: string) => {
    setProjects(current => {
      const previous = current.find(project => project.id === (previousId || song.id));
      const updated = [{ id: song.id, title: song.title, duration: song.duration, updated: new Date().toISOString(), favorite: previous?.favorite },
        ...current.filter(project => project.id !== song.id && project.id !== previousId)].slice(0, 50);
      try { localStorage.setItem(STORAGE, JSON.stringify(updated)); } catch { /* Session still works. */ }
      return updated;
    });
  };
  const openSong = (song: PianoSong, edit = false) => {
    setSeed(song); navigate('piano'); setEditNew(PIANO_EDITION_ENABLED && edit); setError(''); remember(song);
  };
  const openFreePiano = () => {
    setSeed(null); navigate('piano'); setEditNew(false); setError('');
    setPianoSession(session => session + 1);
  };
  const loadProject = async (project: Project) => {
    setLoading(true); setError('');
    try { openSong({ ...await pianoRequest<Omit<PianoSong, 'id'>>(`/jobs/${project.id}/result`), id: project.id }); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Không mở được dự án.'); }
    finally { setLoading(false); }
  };
  const blankScore = async () => {
    setLoading(true); setError('');
    try { openSong(await pianoRequest<PianoSong>('/scores', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'Untitled score', bars: 8, bpm: 100 }) }), true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Không tạo được phổ.'); }
    finally { setLoading(false); }
  };
  const favorite = (id: string) => setProjects(current => {
    const updated = current.map(project => project.id === id ? { ...project, favorite: !project.favorite } : project);
    try { localStorage.setItem(STORAGE, JSON.stringify(updated)); } catch { /* Session still works. */ }
    return updated;
  });
  const visible = projects.filter(project => project.title.toLowerCase().includes(search.toLowerCase()) && (view !== 'collections' || project.favorite));

  return (
    <div className={`auralis-workspace ${collapsed ? 'sidebar-collapsed' : ''} ${nativeHost ? 'studio-native-host' : ''}`}>
      <aside className="studio-sidebar">
        <div className="studio-brand"><img className="studio-brand-image" src={logo} alt="Harmony Auralis" /><button onClick={() => setCollapsed(value => !value)} title={collapsed ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'} aria-label={collapsed ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'} aria-expanded={!collapsed}>◫</button></div>
        <nav className="studio-navigation" aria-label="Không gian âm nhạc">
          <button className={view === 'new' ? 'active' : ''} onClick={() => { navigate('new'); setError(''); }} title="New transcription" aria-label="New transcription"><b>＋</b><span>New transcription</span></button>
          <button className={view === 'piano' && !seed ? 'active' : ''} aria-current={view === 'piano' && !seed ? 'page' : undefined} onClick={openFreePiano} title="Piano · Chơi thử và sáng tác" aria-label="Piano"><b aria-hidden="true"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="2.5" y="3" width="19" height="18" rx="2" /><path d="M7.25 3v18M12 3v18M16.75 3v18" /><path d="M6 4h2.5v9H6zm4.75 0h2.5v9h-2.5zm4.75 0H18v9h-2.5z" fill="currentColor" stroke="none" /></svg></b><span>Piano</span></button>
          {PIANO_EDITION_ENABLED && <button onClick={() => void blankScore()} disabled={loading} title="Create a score" aria-label="Create a score"><b>♮</b><span>Create a score</span></button>}
          <div className="studio-nav-divider" />
          <button className={view === 'projects' ? 'active' : ''} onClick={() => navigate('projects')} title="Projects" aria-label="Projects"><b>♫</b><span>Projects</span><em>{projects.length}</em></button>
          <button className={view === 'collections' ? 'active' : ''} onClick={() => navigate('collections')} title="Collections" aria-label="Collections"><b>▥</b><span>Collections</span></button>
          <button onClick={() => { navigate('projects'); requestAnimationFrame(() => searchRef.current?.focus()); }} title="Search" aria-label="Search"><b>⌕</b><span>Search</span></button>
        </nav>
        <div className="studio-recent"><div className="studio-section-label">RECENT PROJECTS</div>{projects.slice(0, 5).map(project => <button key={project.id} onClick={() => void loadProject(project)} title={project.title}><i>♩</i><span>{project.title}</span></button>)}{!projects.length && <p>Bản nhạc của bạn sẽ xuất hiện ở đây.</p>}</div>
        <div className="studio-sidebar-bottom"><button className="studio-home-link" onClick={() => { setSeed(null); navigate('new'); }} title="Về trang chủ">⌂ <span>Về trang chủ</span></button><button className="studio-profile" type="button" onClick={() => setAuthOpen(true)} title="Đăng nhập hoặc đăng ký" aria-label="Đăng nhập hoặc đăng ký"><span className="studio-avatar">A</span><span>Đăng nhập<small>Tạo tài khoản miễn phí</small></span><b>⌄</b></button></div>
      </aside>
      <main className={`studio-main studio-view-${view}`}>
        {error && <div className="studio-error" role="alert">{error}<button onClick={() => setError('')} aria-label="Đóng thông báo">×</button></div>}
        {view === 'new' ? <div className="studio-new">
          <div className="studio-topline"><span>YOUR PERSONAL MUSIC STUDIO</span><span>Âm nhạc, theo cách của bạn <i>✦</i></span></div>
          <div className="studio-welcome"><div className="studio-mark-bubble"><img src={logo} alt="Harmony Auralis" /></div><span className="studio-eyebrow">FROM SOUND TO SOMETHING BEAUTIFUL</span><h1>Hôm nay, bạn muốn<br /><em>chơi bản nhạc nào?</em></h1><p>Một bản thu. Một đường link. Cả thế giới âm nhạc của bạn.</p></div>
          <div className="studio-import-stage" ref={homeStage}>
            <svg className="studio-wave" viewBox="0 0 500 220" aria-hidden="true">{Array.from({ length: 56 }, (_, index) => { const height = 22 + (Math.sin(index * 1.73) + 1) * 45 + (56 - index) * 1.5; return <rect key={index} x={index * 9} y={(220 - height) / 2} width="5" height={height} rx="3" />; })}</svg>
            <div className="studio-notes-decoration" aria-hidden="true">{musicSymbols.map((symbol, index) => <span className="studio-drifting-note" key={index} style={{ top: `${5 + (index * 37) % 86}%`, fontSize: `${30 + (index % 5) * 8}px` }}><i>{symbol}</i></span>)}</div>
            <PianoImport open embedded onClose={() => {}} onImported={openSong} />
          </div>
          <div className="studio-process"><span><b>01</b> Nhập bản nhạc</span><i>⟶</i><span><b>02</b> Để AI lắng nghe</span><i>⟶</i><span><b>03</b> Chơi & sáng tạo</span></div>
          <button className="studio-free-piano" onClick={openFreePiano}>Hoặc mở đàn piano tự do <span>↗</span></button>
          <footer className="studio-page-footer"><span>CRAFTED FOR THE WAY YOU MAKE MUSIC.</span><span>Harmony Auralis Studio</span></footer>
        </div> : view === 'piano' ? <PianoKeyboard apiUrl={apiUrl} nativeHost={nativeHost} key={seed?.id || `free-${pianoSession}`} initialSong={seed} startInEdition={editNew} workspace onNewTranscription={() => navigate('new')} onProjectUpdate={remember} onEditionChange={setCollapsed} /> : <section className="studio-projects"><div className="studio-projects-title"><div><span className="studio-eyebrow">YOUR MUSIC, IN ONE PLACE</span><h1>{view === 'collections' ? 'Bộ sưu tập của bạn' : 'Những bản nhạc của bạn'}</h1></div><button onClick={() => navigate('new')}>＋ New transcription</button></div><input ref={searchRef} className="studio-project-search" placeholder="Tìm tên bản nhạc…" value={search} onChange={event => setSearch(event.target.value)} aria-label="Tìm dự án" /><div className="studio-project-grid">{visible.map(project => <article key={project.id}><div className="studio-project-cover" onClick={() => void loadProject(project)}><StudioMark /><span>PIANO SCORE</span></div><div className="studio-project-meta"><button onClick={() => void loadProject(project)}>{project.title}</button><button aria-label={project.favorite ? 'Bỏ yêu thích' : 'Yêu thích'} aria-pressed={project.favorite || false} onClick={() => favorite(project.id)}>{project.favorite ? '★' : '☆'}</button><span>{Math.floor(project.duration / 60)}:{String(Math.floor(project.duration % 60)).padStart(2, '0')} · {new Date(project.updated).toLocaleDateString('vi-VN')}</span></div></article>)}</div>{!visible.length && <div className="studio-empty"><StudioMark /><h2>{view === 'collections' ? 'Dành chỗ cho những bản nhạc yêu thích.' : 'Bản nhạc đầu tiên đang chờ bạn.'}</h2><p>{view === 'collections' ? 'Đánh dấu sao trong Projects để thêm vào bộ sưu tập.' : 'Tải file hoặc dán link YouTube để bắt đầu.'}</p><button onClick={() => navigate(view === 'collections' ? 'projects' : 'new')}>{view === 'collections' ? 'Mở Projects' : 'New transcription'}</button></div>}</section>}
        {loading && <div className="studio-loading" role="status"><span /> Đang mở không gian âm nhạc…</div>}
      </main>
      {authOpen && <AuthDialog open onClose={() => setAuthOpen(false)} logo={logo} />}
    </div>
  );
}
