import React from 'react';
import { Film, Image as ImageIcon, Music, Sparkles, User } from 'lucide-react';
import type { ModelDefinition, GenerationReferences } from '../../../types/studio';
import { ReferenceSlot } from './ReferenceSlot';

interface ConditioningTrayProps {
  model: ModelDefinition;
  references: GenerationReferences;
  onChange: (refs: GenerationReferences) => void;
}

export const ConditioningTray: React.FC<ConditioningTrayProps> = ({
  model,
  references,
  onChange,
}) => {
  const mediaType = model.mediaType.toLowerCase();
  const caps = model.capabilities || {};
  const maxImageRefs = caps.maxImageRefs ?? (mediaType === 'video' ? 9 : 4);

  const imageRefs = references.imageRefs || [];
  const videoRefs = references.videoRefs || [];

  const handleUpdate = (partial: Partial<GenerationReferences>) => {
    onChange({
      ...references,
      ...partial,
    });
  };

  const isVideo = mediaType === 'video';
  const isImage = mediaType === 'image';
  const isLipSync = mediaType === 'lip_sync';
  const isUpscale = mediaType === 'upscale';

  return (
    <div className="flex items-center gap-2 overflow-x-auto py-1">
      {/* 1. Mode VIDEO : Fentes Start / End / Image refs / Video refs / Audio refs */}
      {isVideo && (
        <>
          <ReferenceSlot
            label="Start frame"
            previewUrl={references.startFrame}
            icon={<Film className="w-4 h-4 text-studio-muted" />}
            onSelectFile={(files) => {
              const url = URL.createObjectURL(files[0]);
              handleUpdate({ startFrame: url });
            }}
            onRemove={() => handleUpdate({ startFrame: null })}
          />

          <ReferenceSlot
            label="End frame"
            previewUrl={references.endFrame}
            icon={<Film className="w-4 h-4 text-studio-muted" />}
            onSelectFile={(files) => {
              const url = URL.createObjectURL(files[0]);
              handleUpdate({ endFrame: url });
            }}
            onRemove={() => handleUpdate({ endFrame: null })}
          />

          <ReferenceSlot
            label="Image refs"
            countBadge={imageRefs.length > 0 ? `${imageRefs.length}/${maxImageRefs}` : undefined}
            isLimitReached={imageRefs.length >= maxImageRefs}
            multiple={true}
            icon={<ImageIcon className="w-4 h-4 text-studio-muted" />}
            onSelectFile={(files) => {
              const newUrls = Array.from(files).map((f) => URL.createObjectURL(f));
              const combined = [...imageRefs, ...newUrls].slice(0, maxImageRefs);
              handleUpdate({ imageRefs: combined });
            }}
            onRemove={() => handleUpdate({ imageRefs: [] })}
          />

          <ReferenceSlot
            label="Video refs"
            countBadge={videoRefs.length > 0 ? `${videoRefs.length} ref` : undefined}
            accept="video/*"
            icon={<Film className="w-4 h-4 text-studio-muted" />}
            onSelectFile={(files) => {
              const url = URL.createObjectURL(files[0]);
              handleUpdate({ videoRefs: [...videoRefs, url] });
            }}
            onRemove={() => handleUpdate({ videoRefs: [] })}
          />

          <ReferenceSlot
            label="Audio refs"
            previewUrl={references.audioRef}
            accept="audio/*"
            icon={<Music className="w-4 h-4 text-studio-muted" />}
            onSelectFile={(files) => {
              const url = URL.createObjectURL(files[0]);
              handleUpdate({ audioRef: url });
            }}
            onRemove={() => handleUpdate({ audioRef: null })}
          />
        </>
      )}

      {/* 2. Mode IMAGE : Fente Image refs */}
      {isImage && (
        <ReferenceSlot
          label="Image refs"
          countBadge={imageRefs.length > 0 ? `${imageRefs.length}/${maxImageRefs}` : undefined}
          isLimitReached={imageRefs.length >= maxImageRefs}
          multiple={true}
          icon={<ImageIcon className="w-4 h-4 text-studio-muted" />}
          onSelectFile={(files) => {
            const newUrls = Array.from(files).map((f) => URL.createObjectURL(f));
            const combined = [...imageRefs, ...newUrls].slice(0, maxImageRefs);
            handleUpdate({ imageRefs: combined });
          }}
          onRemove={() => handleUpdate({ imageRefs: [] })}
        />
      )}

      {/* 3. Mode LIP SYNC : Face reference + Voice track */}
      {isLipSync && (
        <>
          <ReferenceSlot
            label="Face reference"
            previewUrl={references.startFrame}
            icon={<User className="w-4 h-4 text-studio-muted" />}
            onSelectFile={(files) => {
              const url = URL.createObjectURL(files[0]);
              handleUpdate({ startFrame: url });
            }}
            onRemove={() => handleUpdate({ startFrame: null })}
          />

          <ReferenceSlot
            label="Voice track"
            previewUrl={references.audioRef}
            accept="audio/*"
            icon={<Music className="w-4 h-4 text-studio-muted" />}
            onSelectFile={(files) => {
              const url = URL.createObjectURL(files[0]);
              handleUpdate({ audioRef: url });
            }}
            onRemove={() => handleUpdate({ audioRef: null })}
          />
        </>
      )}

      {/* 4. Mode UPSCALING : Source media */}
      {isUpscale && (
        <ReferenceSlot
          label="Source media"
          previewUrl={references.startFrame}
          accept="image/*,video/*"
          icon={<Sparkles className="w-4 h-4 text-studio-muted" />}
          onSelectFile={(files) => {
            const url = URL.createObjectURL(files[0]);
            handleUpdate({ startFrame: url });
          }}
          onRemove={() => handleUpdate({ startFrame: null })}
        />
      )}
    </div>
  );
};
