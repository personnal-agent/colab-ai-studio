import React, { useRef, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import type { GenerationReferences, ModelDefinition } from '../../../types/studio';
import { ReferenceSlot } from './ReferenceSlot';

export interface ConditioningTrayProps {
  mode: string;
  model?: ModelDefinition | null;
  references: GenerationReferences;
  onReferencesChange: (refs: GenerationReferences) => void;
}

export const ConditioningTray: React.FC<ConditioningTrayProps> = ({
  mode, model, references, onReferencesChange,
}) => {
  const caps = model?.capabilities;
  const supportsFirstFrame = mode === 'video' ? (caps?.supportsFirstFrame ?? true) : false;
  const supportsLastFrame = mode === 'video' ? (caps?.supportsLastFrame ?? true) : false;
  const supportsVideoRef = caps?.supportsVideoRef ?? true;
  const maxImageRefs = caps?.maxImageRefs ?? 9;
  const maxVideoRefs = caps?.maxVideoRefs ?? 1;

  const imageRefs = references.imageRefs ?? [];
  const videoRefs = references.videoRefs ?? [];
  const isImageOverLimit = imageRefs.length > maxImageRefs;
  const isVideoOverLimit = videoRefs.length > maxVideoRefs;
  const isOverLimit = isImageOverLimit || isVideoOverLimit;

  const canAddImage = imageRefs.length < maxImageRefs;
  const canAddVideo = supportsVideoRef && videoRefs.length < maxVideoRefs;
  const canAddIngredient = !isOverLimit && (canAddImage || canAddVideo);
  const ingredientAccept = canAddVideo ? (canAddImage ? 'image/*,video/*' : 'video/*') : 'image/*';

  // Gestion propriétaire du cycle de vie des Object URLs créées localement
  const createdUrlsRef = useRef<Set<string>>(new Set());

  const safeRevoke = (url?: string | null) => {
    if (url && typeof url === 'string' && url.startsWith('blob:') && createdUrlsRef.current.has(url)) {
      try { URL.revokeObjectURL(url); } catch { /* ignore */ }
      createdUrlsRef.current.delete(url);
    }
  };

  // Synchronisation des révocations lors des réinitialisations parentes
  const prevRefsRef = useRef(references);
  useEffect(() => {
    const prev = prevRefsRef.current;
    const current = new Set<string>([
      references.startFrame, references.endFrame, references.upscaleSource,
      ...(references.imageRefs || []), ...(references.videoRefs || []), ...(references.audioRefs || []),
    ].filter((u): u is string => Boolean(u)));

    const checkAndRevoke = (url?: string | null) => {
      if (url && !current.has(url)) safeRevoke(url);
    };
    [prev.startFrame, prev.endFrame, prev.upscaleSource, ...(prev.imageRefs || []), ...(prev.videoRefs || []), ...(prev.audioRefs || [])].forEach(checkAndRevoke);
    prevRefsRef.current = references;
  });

  // Nettoyage au démontage
  useEffect(() => {
    const localUrls = createdUrlsRef.current;
    return () => {
      localUrls.forEach((url) => { try { URL.revokeObjectURL(url); } catch { /* ignore */ } });
      localUrls.clear();
    };
  }, []);

  const handleFileSelect = (
    slotType: 'startFrame' | 'endFrame' | 'upscaleSource' | 'lipSyncImage' | 'lipSyncAudio' | 'ingredient',
    file: File
  ) => {
    const blobUrl = URL.createObjectURL(file);
    createdUrlsRef.current.add(blobUrl);

    if (slotType === 'startFrame') {
      safeRevoke(references.startFrame);
      onReferencesChange({ ...references, startFrame: blobUrl });
    } else if (slotType === 'endFrame') {
      safeRevoke(references.endFrame);
      onReferencesChange({ ...references, endFrame: blobUrl });
    } else if (slotType === 'upscaleSource') {
      const isVideo = file.type.startsWith('video/') || /\.(mp4|webm|mov|mkv)$/i.test(file.name);
      safeRevoke(references.upscaleSource);
      onReferencesChange({ ...references, upscaleSource: blobUrl, upscaleSourceType: isVideo ? 'video' : 'image' });
    } else if (slotType === 'lipSyncImage') {
      references.imageRefs?.forEach(safeRevoke);
      onReferencesChange({ ...references, imageRefs: [blobUrl] });
    } else if (slotType === 'lipSyncAudio') {
      references.audioRefs?.forEach(safeRevoke);
      onReferencesChange({ ...references, audioRefs: [blobUrl] });
    } else if (slotType === 'ingredient') {
      const isVideo = file.type.startsWith('video/') || /\.(mp4|webm|mov|mkv)$/i.test(file.name);
      if (isVideo) {
        if (!supportsVideoRef || videoRefs.length >= maxVideoRefs) { safeRevoke(blobUrl); return; }
        onReferencesChange({ ...references, videoRefs: [...videoRefs, blobUrl] });
      } else {
        if (imageRefs.length >= maxImageRefs) { safeRevoke(blobUrl); return; }
        onReferencesChange({ ...references, imageRefs: [...imageRefs, blobUrl] });
      }
    }
  };

  const removeIngredient = (idx: number, isVideo: boolean) => {
    if (isVideo) {
      safeRevoke(videoRefs[idx]);
      onReferencesChange({ ...references, videoRefs: videoRefs.filter((_, i) => i !== idx) });
    } else {
      safeRevoke(imageRefs[idx]);
      onReferencesChange({ ...references, imageRefs: imageRefs.filter((_, i) => i !== idx) });
    }
  };

  if (mode === 'llm' || mode === 'text') return null;

  return (
    <div className="w-full flex flex-col gap-2 pt-1 pb-2">
      {isOverLimit && (
        <div className="flex items-center gap-1.5 text-xs text-rose-600 bg-rose-50 px-3 py-1 rounded-lg border border-rose-200">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>
            {isVideoOverLimit && isImageOverLimit
              ? `Limite de références (images et vidéos) dépassée. Retirez des ingrédients.`
              : isVideoOverLimit
              ? `Limite de références (vidéos) dépassée (${videoRefs.length}/${maxVideoRefs} max). Retirez des vidéos.`
              : `Limite de références (images) dépassée (${imageRefs.length}/${maxImageRefs} max). Retirez des images.`}
          </span>
        </div>
      )}

      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-1">
        {mode === 'video' && (
          <>
            {supportsFirstFrame && (
              <ReferenceSlot
                label="Start frame" fileUrl={references.startFrame} accept="image/*"
                onFileSelected={(f: File) => handleFileSelect('startFrame', f)}
                onClear={() => { safeRevoke(references.startFrame); onReferencesChange({ ...references, startFrame: null }); }}
              />
            )}
            {supportsLastFrame && (
              <ReferenceSlot
                label="End frame" fileUrl={references.endFrame} accept="image/*"
                onFileSelected={(f: File) => handleFileSelect('endFrame', f)}
                onClear={() => { safeRevoke(references.endFrame); onReferencesChange({ ...references, endFrame: null }); }}
              />
            )}
            {imageRefs.map((url, idx) => (
              <ReferenceSlot
                key={`img-ref-${url}-${idx}`} label={`Réf ${idx + 1}`} badge={`Réf ${idx + 1}`}
                fileUrl={url} isWarning={isOverLimit} onClear={() => removeIngredient(idx, false)}
              />
            ))}
            {videoRefs.map((url, idx) => (
              <ReferenceSlot
                key={`vid-ref-${url}-${idx}`} label={`Vidéo ${idx + 1}`} badge="N-1"
                mediaType="video" fileUrl={url} isWarning={isOverLimit} onClear={() => removeIngredient(idx, true)}
              />
            ))}
            {canAddIngredient && (
              <ReferenceSlot
                label="+ Ingrédient" accept={ingredientAccept}
                onFileSelected={(f: File) => handleFileSelect('ingredient', f)}
              />
            )}
          </>
        )}

        {mode === 'image' && (
          <>
            {imageRefs.map((url, idx) => (
              <ReferenceSlot
                key={`img-ref-${url}-${idx}`} label={`Réf ${idx + 1}`} badge={`Réf ${idx + 1}`}
                fileUrl={url} onClear={() => removeIngredient(idx, false)}
              />
            ))}
            {imageRefs.length < (caps?.maxImageRefs ?? 4) && (
              <ReferenceSlot
                label="+ Réf Image" accept="image/*"
                onFileSelected={(f: File) => handleFileSelect('ingredient', f)}
              />
            )}
          </>
        )}

        {mode === 'lip_sync' && (
          <>
            <ReferenceSlot
              label="Portrait source" fileUrl={imageRefs[0] || null} accept="image/*"
              onFileSelected={(f: File) => handleFileSelect('lipSyncImage', f)}
              onClear={() => { imageRefs.forEach(safeRevoke); onReferencesChange({ ...references, imageRefs: [] }); }}
            />
            <ReferenceSlot
              label="Voix / Audio vocal" mediaType="audio" fileUrl={references.audioRefs?.[0] || null} accept="audio/*"
              onFileSelected={(f: File) => handleFileSelect('lipSyncAudio', f)}
              onClear={() => { references.audioRefs?.forEach(safeRevoke); onReferencesChange({ ...references, audioRefs: [] }); }}
            />
          </>
        )}

        {mode === 'upscale' && (
          <ReferenceSlot
            label="Média source" fileUrl={references.upscaleSource}
            mediaType={references.upscaleSourceType || 'image'} accept="image/*,video/*"
            onFileSelected={(f: File) => handleFileSelect('upscaleSource', f)}
            onClear={() => { safeRevoke(references.upscaleSource); onReferencesChange({ ...references, upscaleSource: null, upscaleSourceType: null }); }}
          />
        )}
      </div>
    </div>
  );
};
