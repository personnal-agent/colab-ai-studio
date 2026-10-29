"""
Hilo SQLite Migrations Registry (0001 to 0019).
Defines the schema for the 46 tables of .hilo/index.sqlite across 7 domains.
"""

MIGRATIONS: list[tuple[str, str]] = [
    (
        "0001_workspaces",
        """
        CREATE TABLE IF NOT EXISTS workspaces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            root_path TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS workspace_members (
            workspace_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'editor',
            permissions_mask INTEGER DEFAULT 0,
            PRIMARY KEY (workspace_id, user_id),
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0002_projects",
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            storage_path TEXT,
            default_brand_kit_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS project_settings (
            project_id TEXT PRIMARY KEY,
            settings_json TEXT NOT NULL DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0003_canvas_documents",
        """
        CREATE TABLE IF NOT EXISTS canvas_documents (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            viewport_x REAL DEFAULT 0.0,
            viewport_y REAL DEFAULT 0.0,
            zoom_level REAL DEFAULT 100.0,
            width REAL DEFAULT 1920.0,
            height REAL DEFAULT 1080.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS canvas_snapshots (
            id TEXT PRIMARY KEY,
            canvas_id TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            payload_blob BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (canvas_id) REFERENCES canvas_documents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS canvas_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canvas_id TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            delta_patch_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (canvas_id) REFERENCES canvas_documents(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0004_layers",
        """
        CREATE TABLE IF NOT EXISTS layers (
            id TEXT PRIMARY KEY,
            canvas_id TEXT NOT NULL,
            parent_id TEXT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            x REAL DEFAULT 0.0,
            y REAL DEFAULT 0.0,
            width REAL DEFAULT 100.0,
            height REAL DEFAULT 100.0,
            z_index INTEGER DEFAULT 0,
            opacity REAL DEFAULT 1.0,
            blend_mode TEXT DEFAULT 'normal',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (canvas_id) REFERENCES canvas_documents(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS layer_properties (
            layer_id TEXT NOT NULL,
            prop_key TEXT NOT NULL,
            prop_value_json TEXT NOT NULL,
            is_animated INTEGER DEFAULT 0,
            PRIMARY KEY (layer_id, prop_key),
            FOREIGN KEY (layer_id) REFERENCES layers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS layer_transforms (
            layer_id TEXT PRIMARY KEY,
            matrix_json TEXT NOT NULL DEFAULT '[1,0,0,0,1,0,0,0,1]',
            rotation_deg REAL DEFAULT 0.0,
            scale_x REAL DEFAULT 1.0,
            scale_y REAL DEFAULT 1.0,
            skew_x REAL DEFAULT 0.0,
            skew_y REAL DEFAULT 0.0,
            FOREIGN KEY (layer_id) REFERENCES layers(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0005_masks_groups",
        """
        CREATE TABLE IF NOT EXISTS layer_masks (
            id TEXT PRIMARY KEY,
            target_layer_id TEXT NOT NULL,
            mask_resource_id TEXT NOT NULL,
            invert_mask INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (target_layer_id) REFERENCES layers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS layer_groups (
            id TEXT PRIMARY KEY,
            group_name TEXT NOT NULL,
            collapsed INTEGER DEFAULT 0,
            pass_through_mode INTEGER DEFAULT 1
        );
        """,
    ),
    (
        "0006_timelines",
        """
        CREATE TABLE IF NOT EXISTS timelines (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            canvas_id TEXT,
            duration_sec REAL DEFAULT 10.0,
            fps INTEGER DEFAULT 30,
            total_frames INTEGER DEFAULT 300,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS timeline_tracks (
            id TEXT PRIMARY KEY,
            timeline_id TEXT NOT NULL,
            track_index INTEGER NOT NULL,
            track_type TEXT NOT NULL,
            is_muted INTEGER DEFAULT 0,
            is_locked INTEGER DEFAULT 0,
            FOREIGN KEY (timeline_id) REFERENCES timelines(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS timeline_markers (
            id TEXT PRIMARY KEY,
            timeline_id TEXT NOT NULL,
            frame_number INTEGER NOT NULL,
            label TEXT NOT NULL,
            color_hex TEXT DEFAULT '#6366F1',
            FOREIGN KEY (timeline_id) REFERENCES timelines(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0007_timeline_clips",
        """
        CREATE TABLE IF NOT EXISTS timeline_clips (
            id TEXT PRIMARY KEY,
            track_id TEXT NOT NULL,
            resource_id TEXT,
            start_frame INTEGER NOT NULL,
            duration_frames INTEGER NOT NULL,
            in_point INTEGER DEFAULT 0,
            out_point INTEGER,
            speed_factor REAL DEFAULT 1.0,
            FOREIGN KEY (track_id) REFERENCES timeline_tracks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS timeline_keyframes (
            id TEXT PRIMARY KEY,
            clip_id TEXT NOT NULL,
            parameter_name TEXT NOT NULL,
            frame_number INTEGER NOT NULL,
            value_float REAL NOT NULL,
            easing_type TEXT DEFAULT 'linear',
            FOREIGN KEY (clip_id) REFERENCES timeline_clips(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS timeline_transitions (
            id TEXT PRIMARY KEY,
            from_clip_id TEXT NOT NULL,
            to_clip_id TEXT NOT NULL,
            transition_type TEXT NOT NULL,
            duration_frames INTEGER DEFAULT 15,
            FOREIGN KEY (from_clip_id) REFERENCES timeline_clips(id) ON DELETE CASCADE,
            FOREIGN KEY (to_clip_id) REFERENCES timeline_clips(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0008_resource_v3",
        """
        CREATE TABLE IF NOT EXISTS resource_v3 (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            generation_id TEXT NOT NULL,
            artifact_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            sha256_digest TEXT NOT NULL,
            byte_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            media_type TEXT NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'committed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_resource_key UNIQUE (workspace_id, generation_id, artifact_id)
        );

        CREATE INDEX IF NOT EXISTS idx_resource_v3_workspace ON resource_v3(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_resource_v3_media_type ON resource_v3(media_type);
        CREATE INDEX IF NOT EXISTS idx_resource_v3_digest ON resource_v3(sha256_digest);
        """,
    ),
    (
        "0009_resource_variants_tags",
        """
        CREATE TABLE IF NOT EXISTS resource_variants (
            id TEXT PRIMARY KEY,
            resource_id TEXT NOT NULL,
            variant_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resource_id) REFERENCES resource_v3(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resource_tags (
            resource_id TEXT NOT NULL,
            tag_label TEXT NOT NULL,
            PRIMARY KEY (resource_id, tag_label),
            FOREIGN KEY (resource_id) REFERENCES resource_v3(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0010_asset_collections",
        """
        CREATE TABLE IF NOT EXISTS asset_collections (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            collection_name TEXT NOT NULL,
            icon_name TEXT DEFAULT 'folder',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS asset_collection_items (
            collection_id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            PRIMARY KEY (collection_id, resource_id),
            FOREIGN KEY (collection_id) REFERENCES asset_collections(id) ON DELETE CASCADE,
            FOREIGN KEY (resource_id) REFERENCES resource_v3(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0011_journal_staging",
        """
        CREATE TABLE IF NOT EXISTS journal_staging_no_replace (
            operation_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            generation_id TEXT NOT NULL,
            artifact_id TEXT NOT NULL,
            temp_path TEXT NOT NULL,
            final_path TEXT NOT NULL,
            sha256_digest TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_journal_status ON journal_staging_no_replace(status);
        CREATE INDEX IF NOT EXISTS idx_journal_lookup
        ON journal_staging_no_replace(workspace_id, generation_id, artifact_id);
        """,
    ),
    (
        "0012_agent_sessions",
        """
        CREATE TABLE IF NOT EXISTS agent_sessions (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            title TEXT NOT NULL,
            active_agent TEXT DEFAULT 'leader',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            stage TEXT DEFAULT 'dialogue',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0013_agent_plans",
        """
        CREATE TABLE IF NOT EXISTS agent_plans (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            goal_description TEXT NOT NULL,
            status TEXT DEFAULT 'in_progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS agent_tasks (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            step_index INTEGER NOT NULL,
            title TEXT NOT NULL,
            assignee TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (plan_id) REFERENCES agent_plans(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS agent_contracts (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            contract_name TEXT NOT NULL,
            passed INTEGER NOT NULL DEFAULT 1,
            report_json TEXT DEFAULT '{}',
            FOREIGN KEY (task_id) REFERENCES agent_tasks(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0014_agent_tools_memory",
        """
        CREATE TABLE IF NOT EXISTS agent_tool_invocations (
            id TEXT PRIMARY KEY,
            message_id TEXT,
            tool_name TEXT NOT NULL,
            input_json TEXT NOT NULL,
            output_json TEXT,
            duration_ms INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_memory_vectors (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            context_key TEXT NOT NULL,
            vector_blob BLOB,
            FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS agent_state_checkpoints (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            checkpoint_hash TEXT NOT NULL,
            state_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0015_brand_kits",
        """
        CREATE TABLE IF NOT EXISTS brand_kits (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            brand_name TEXT NOT NULL,
            source_url TEXT,
            primary_colors_hex TEXT DEFAULT '[]',
            typography_family TEXT,
            tone_overview TEXT,
            visual_guidelines TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS brand_kit_assets (
            brand_kit_id TEXT NOT NULL,
            asset_role TEXT NOT NULL,
            file_path TEXT NOT NULL,
            PRIMARY KEY (brand_kit_id, asset_role),
            FOREIGN KEY (brand_kit_id) REFERENCES brand_kits(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0016_loras_presets",
        """
        CREATE TABLE IF NOT EXISTS lora_configs (
            id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            file_name TEXT NOT NULL,
            trigger_words_json TEXT DEFAULT '[]',
            base_architecture TEXT NOT NULL,
            default_weight REAL DEFAULT 0.8,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS lora_weights_cache (
            lora_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            compiled_weight_hash TEXT NOT NULL,
            PRIMARY KEY (lora_id, model_id),
            FOREIGN KEY (lora_id) REFERENCES lora_configs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS model_presets (
            id TEXT PRIMARY KEY,
            model_id TEXT NOT NULL,
            preset_name TEXT NOT NULL,
            parameters_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS prompt_templates (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            template_body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ),
    (
        "0017_character_anchors",
        """
        CREATE TABLE IF NOT EXISTS character_anchors (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            name TEXT NOT NULL,
            trigger_token TEXT NOT NULL,
            avatar_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS character_anchor_frames (
            character_id TEXT NOT NULL,
            angle_index INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            PRIMARY KEY (character_id, angle_index),
            FOREIGN KEY (character_id) REFERENCES character_anchors(id) ON DELETE CASCADE
        );
        """,
    ),
    (
        "0018_inference_tasks",
        """
        CREATE TABLE IF NOT EXISTS inference_tasks (
            id TEXT PRIMARY KEY,
            generation_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            media_type TEXT NOT NULL,
            execution_mode TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            progress_percent REAL DEFAULT 0.0,
            worker_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS inference_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES inference_tasks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS slot_memoire_modele (
            slot_id TEXT PRIMARY KEY,
            total_memory_gb REAL NOT NULL,
            free_memory_gb REAL NOT NULL,
            is_available INTEGER DEFAULT 1,
            loaded_lora_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS model_swap_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evicted_model_id TEXT,
            loaded_model_id TEXT NOT NULL,
            freed_vram_gb REAL DEFAULT 0.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ),
    (
        "0019_telemetry_audit",
        """
        CREATE TABLE IF NOT EXISTS hardware_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu_usage_pct REAL NOT NULL,
            host_ram_used_mb REAL NOT NULL,
            temperature_c REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS contract_violations_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            violation_type TEXT NOT NULL,
            details_json TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ),
]
