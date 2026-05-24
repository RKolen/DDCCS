import * as React from 'react';

interface ImageLightboxProps {
  src:     string;
  alt:     string;
  onClose: () => void;
}

export function ImageLightbox({ src, alt, onClose }: ImageLightboxProps): React.ReactElement {
  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div className="lightbox-backdrop" onClick={onClose}>
      <img className="lightbox-img" src={src} alt={alt} onClick={e => e.stopPropagation()} />
    </div>
  );
}
