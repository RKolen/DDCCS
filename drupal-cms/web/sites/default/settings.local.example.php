<?php

/**
 * Local developer overrides — copy to settings.local.php and customise.
 *
 * This file is NOT committed. Set values here instead of in settings.php
 * or config sync so that model names, hosts, and credentials never appear
 * in version control.
 *
 * Alternatively, set these as environment variables in your .ddev/.env file
 * or via `ddev config --web-environment=KEY=value`.
 */

// AI providers — set the provider and model you run locally.
// $config['ai.settings']['default_providers']['chat']['provider_id']       = 'ollama';
// $config['ai.settings']['default_providers']['chat']['model_id']           = 'your-chat-model';
// $config['ai.settings']['default_providers']['embeddings']['provider_id'] = 'ollama';
// $config['ai.settings']['default_providers']['embeddings']['model_id']    = 'your-embeddings-model';
// $config['ai.settings']['default_vdb_provider']                            = 'milvus';

// Ollama host (defaults to localhost:11434 inside DDEV).
// $config['ai_provider_ollama.settings']['host_name'] =

// Milvus host.
// $config['ai_vdb_provider_milvus.settings']['server'] =