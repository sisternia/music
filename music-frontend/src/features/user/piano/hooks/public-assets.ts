/** Expo DOM bundles use a local asset prefix in native binaries. */
export function pianoPublicAsset(path: string) {
  const base = process.env.EXPO_BASE_URL || '/';
  return `${base.replace(/\/?$/, '/')}${path.replace(/^\//, '')}`;
}
