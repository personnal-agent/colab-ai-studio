import React from 'react';
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
  mode,
  model,
  references,
  onReferencesChange,
}) => {
  // Masquage total en mode LLM
  if (mode === 'llm' || mode === 'text') {
    return null;
  }

  const caps = model?.capabilities;
  const maxImageRefs = caps?.maxImageRefs ?? 9;
  const imageRefs = references.imageRefs ?? [];
  const videoRefs = references.videoRefs ?? [];
  const totalRefsCount = imageRefs.length + videoRefs.length;
  const isOverLimit = totalRefsCount > maxImageRefs;

  const handleFileSelect = (slotType: 'startFrame' | 'endFrame' | 'upscaleSource' | 'lipSyncImage' | 'lipSyncAudio' | 'ingredient', file: File) => {
    const blobUrl = URL.createObjectURL(file);
    if (slotType === 'startFrame') {
      onReferencesChange({ ...references, startFrame: blobUrl });
    } else if (slotType === 'endFrame') {
      onReferencesChange({ ...references, endFrame: blobUrl });
    } else if (slotType === 'upscaleSource') {
      onReferencesChange({ ...references, upscaleSource: blobUrl });
    } else if (slotType === 'lipSyncImage') {
      onReferencesChange({ ...references, imageRefs: [blobUrl] });
    } else if (slotType === 'lipSyncAudio') {
      onReferencesChange({ ...references, audioRefs: [blobUrl] });
    } else if (slotType === 'ingredient') {
      if (file.type.startsWith('video/')) {
        onReferencesChange({ ...references, videoRefs: [...videoRefs, blobUrl] });
      } else {
        onReferencesChange({ ...references, imageRefs: [...imageRefs, blobUrl] });
      }
    }
  };

  const removeIngredient = (idx: number, isVideo: boolean) => {
    if (isVideo) {
      onReferencesChange({
        ...references,
        videoRefs: videoRefs.filter((_, i) => i !== idx),
      });
    } else {
      onReferencesChange({
        ...references,
        imageRefs: imageRefs.filter((_, i) => i !== idx),
      });
    }
  };

  if (mode === 'llm' || mode === 'text') {
    return null;
  }

  return (
    <div className="w-full flex flex-col gap-2 pt-1 pb-2">
      {isOverLimit && (
        <div className="flex items-center gap-1.5 text-xs text-rose-600 bg-rose-50 px-3 py-1 rounded-lg border border-rose-200">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>Limite de références dépassée ({totalRefsCount}/{maxImageRefs} max). Retirez des ingrédients.</span>
        </div>
      )}

      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-1">
        {/* --- PÔLE VIDÉO : SUBSOMPTION COMPLÈTE --- */}
        {mode === 'video' && (
          <>
            {/* 1. Start Frame */}
            <ReferenceSlot
              label="Start frame"
              fileUrl={references.startFrame}
              accept="image/*"
              onFileSelected={(f: File) => handleFileSelect('startFrame', f)}
              onClear={() => onReferencesChange({ ...references, startFrame: null })}
            />

            {/* 2. End Frame */}
            <ReferenceSlot
              label="End frame"
              fileUrl={references.endFrame}
              accept="image/*"
              onFileSelected={(f: File) => handleFileSelect('endFrame', f)}
              onClear={() => onReferencesChange({ ...references, endFrame: null })}
            />

            {/* 3. Ingrédients existants (Images) */}
            {imageRefs.map((url, idx) => (
              <ReferenceSlot
                key={`img-ref-${url}-${idx}`}
                label={`Réf ${idx + 1}`}
                badge={`Réf ${idx + 1}`}
                fileUrl={url}
                isWarning={isOverLimit}
                onClear={() => removeIngredient(idx, false)}
              />
            ))}

            {/* 4. Ingrédients existants (Vidéos N-1 / Video-as-Ingredient) */}
            {videoRefs.map((url, idx) => (
              <ReferenceSlot
                key={`vid-ref-${url}-${idx}`}
                label={`Vidéo ${idx + 1}`}
                badge="N-1"
                mediaType="video"
                fileUrl={url}
                isWarning={isOverLimit}
                onClear={() => removeIngredient(idx, true)}
              />
            ))}

            {/* 5. Fente d'ajout d'ingrédient */}
            {!isOverLimit && totalRefsCount < maxImageRefs && (
              <ReferenceSlot
                label="+ Ingrédient"
                accept="image/*,video/*"
                onFileSelected={(f: File) => handleFileSelect('ingredient', f)}
              />
            )}
          </>
        )}

        {/* --- PÔLE IMAGE --- */}
        {mode === 'image' && (
          <>
            {imageRefs.map((url, idx) => (
              <ReferenceSlot
                key={`img-ref-${url}-${idx}`}
                label={`Réf ${idx + 1}`}
                badge={`Réf ${idx + 1}`}
                fileUrl={url}
                onClear={() => removeIngredient(idx, false)}
              />
            ))}
            {imageRefs.length < (caps?.maxImageRefs ?? 4) && (
              <ReferenceSlot
                label="+ Réf Image"
                accept="image/*"
                onFileSelected={(f: File) => handleFileSelect('ingredient', f)}
              />
            )}
          </>
        )}

        {/* --- PÔLE LIP SYNC --- */}
        {mode === 'lip_sync' && (
          <>
            <ReferenceSlot
              label="Portrait source"
              fileUrl={imageRefs[0] || null}
              accept="image/*"
              onFileSelected={(f: File) => handleFileSelect('lipSyncImage', f)}
              onClear={() => onReferencesChange({ ...references, imageRefs: [] })}
            />
            <ReferenceSlot
              label="Voix / Audio vocal"
              mediaType="audio"
              fileUrl={references.audioRefs?.[0] || null}
              accept="audio/*"
              onFileSelected={(f: File) => handleFileSelect('lipSyncAudio', f)}
              onClear={() => onReferencesChange({ ...references, audioRefs: [] })}
            />
          </>
        )}

        {/* --- PÔLE REHAUSSEMENT / UPSCALE --- */}
        {mode === 'upscale' && (
          <ReferenceSlot
            label="Média source"
            fileUrl={references.upscaleSource}
            accept="image/*,video/*"
            onFileSelected={(f: File) => handleFileSelect('upscaleSource', f)}
            onClear={() => onReferencesChange({ ...references, upscaleSource: null })}
          />
        )}
      </div>
    </div>
  );
};
