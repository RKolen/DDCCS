<?php

/**
 * @file
 * PHPUnit bootstrap for dnd_search unit tests.
 *
 * Registers PSR-4 namespaces for the module and its tests so PHPUnit can
 * autoload classes without a full Drupal bootstrap.
 */

declare(strict_types=1);

$loader = require __DIR__ . '/../../../../../vendor/autoload.php';

$moduleRoot = __DIR__ . '/..';
$webRoot = __DIR__ . '/../../../../../web';
$contrib = $webRoot . '/modules/contrib';

// Custom module under test.
$loader->addPsr4('Drupal\\dnd_search\\', $moduleRoot . '/src/');
$loader->addPsr4('Drupal\\Tests\\dnd_search\\', __DIR__ . '/src/');

// Contrib modules referenced by dnd_search services (needed for mocking).
$loader->addPsr4('Drupal\\ai\\', $contrib . '/ai/src/');
$loader->addPsr4('Drupal\\search_api\\', $contrib . '/search_api/src/');
