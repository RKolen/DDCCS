<?php

declare(strict_types=1);

namespace Drupal\entity_lock;

use Drupal\Core\Config\ConfigFactoryInterface;
use Drupal\Core\Entity\EntityInterface;
use Drupal\Core\Messenger\MessengerInterface;
use Drupal\Core\StringTranslation\StringTranslationTrait;
use Symfony\Component\HttpFoundation\RequestStack;

/**
 * Manages locked entity configuration and provides access check helpers.
 *
 * Entities added to the locked list are protected from deletion. Entities that
 * implement EntityPublishedInterface are additionally protected from being
 * unpublished (which would otherwise serve as an indirect workaround).
 */
class EntityLockManager {

  use StringTranslationTrait;

  /**
   * The config factory.
   *
   * @var \Drupal\Core\Config\ConfigFactoryInterface
   */
  protected ConfigFactoryInterface $configFactory;

  /**
   * The messenger service.
   *
   * @var \Drupal\Core\Messenger\MessengerInterface
   */
  protected MessengerInterface $messenger;

  /**
   * The request stack.
   *
   * @var \Symfony\Component\HttpFoundation\RequestStack
   */
  protected RequestStack $requestStack;

  /**
   * Constructs an EntityLockManager.
   *
   * @param \Drupal\Core\Config\ConfigFactoryInterface $config_factory
   *   The config factory.
   * @param \Drupal\Core\Messenger\MessengerInterface $messenger
   *   The messenger service.
   * @param \Symfony\Component\HttpFoundation\RequestStack $request_stack
   *   The request stack.
   */
  public function __construct(
    ConfigFactoryInterface $config_factory,
    MessengerInterface $messenger,
    RequestStack $request_stack,
  ) {
    $this->configFactory = $config_factory;
    $this->messenger = $messenger;
    $this->requestStack = $request_stack;
  }

  /**
   * Returns all locked entity entries from configuration.
   *
   * @return array<int, array<string, string>>
   *   An indexed array of entries, each with keys 'entity_type', 'entity_id',
   *   and 'reason'.
   */
  public function getLockedEntities(): array {
    /** @var array<int, array<string, string>> $entries */
    $entries = $this->configFactory->get('entity_lock.settings')->get('locked_entities') ?? [];
    return $entries;
  }

  /**
   * Checks whether a given entity is in the locked list.
   *
   * @param \Drupal\Core\Entity\EntityInterface $entity
   *   The entity to check.
   *
   * @return bool
   *   TRUE if the entity is locked, FALSE otherwise.
   */
  public function isEntityLocked(EntityInterface $entity): bool {
    $entity_type_id = $entity->getEntityTypeId();
    $entity_id = (string) $entity->id();
    foreach ($this->getLockedEntities() as $entry) {
      if (($entry['entity_type'] ?? '') === $entity_type_id && ($entry['entity_id'] ?? '') === $entity_id) {
        return TRUE;
      }
    }
    return FALSE;
  }

  /**
   * Returns the configured lock reason for an entity.
   *
   * @param \Drupal\Core\Entity\EntityInterface $entity
   *   The entity to look up.
   *
   * @return string
   *   The reason string, or an empty string when no reason is configured.
   */
  public function getReasonForEntity(EntityInterface $entity): string {
    $entity_type_id = $entity->getEntityTypeId();
    $entity_id = (string) $entity->id();
    foreach ($this->getLockedEntities() as $entry) {
      if (($entry['entity_type'] ?? '') === $entity_type_id && ($entry['entity_id'] ?? '') === $entity_id) {
        return $entry['reason'] ?? '';
      }
    }
    return '';
  }

  /**
   * Adds a messenger warning when a locked entity cannot be deleted.
   *
   * The message is only added when the current request path contains
   * '/delete', keeping it silent in other contexts (e.g. bulk operations where
   * messages per entity would be noisy on the operation results page).
   *
   * @param \Drupal\Core\Entity\EntityInterface $entity
   *   The entity whose deletion was blocked.
   * @param string $reason
   *   An optional reason explaining why the entity is locked.
   */
  public function showLockedMessage(EntityInterface $entity, string $reason = ''): void {
    $request = $this->requestStack->getCurrentRequest();
    if ($request === NULL || !str_contains($request->getRequestUri(), '/delete')) {
      return;
    }
    $type_label = $entity->getEntityType()->getLabel();
    $entity_label = $entity->label() ?? (string) $entity->id();
    if ($reason !== '') {
      $this->messenger->addWarning($this->t(
        'The @type "@label" is locked and cannot be deleted. Reason: @reason',
        [
          '@type' => $type_label,
          '@label' => $entity_label,
          '@reason' => $reason,
        ],
      ));
      return;
    }
    $this->messenger->addWarning($this->t(
      'The @type "@label" is locked and cannot be deleted.',
      [
        '@type' => $type_label,
        '@label' => $entity_label,
      ],
    ));
  }

  /**
   * Locks an entity, preventing its deletion.
   *
   * If the entity is already locked this is a no-op.
   *
   * @param string $entity_type
   *   The entity type machine name (e.g. 'node', 'taxonomy_term').
   * @param string $entity_id
   *   The entity ID as a string.
   * @param string $reason
   *   An optional human-readable reason for the lock.
   */
  public function lockEntity(string $entity_type, string $entity_id, string $reason = ''): void {
    $config = $this->configFactory->getEditable('entity_lock.settings');
    /** @var array<int, array<string, string>> $entries */
    $entries = $config->get('locked_entities') ?? [];
    foreach ($entries as $entry) {
      if (($entry['entity_type'] ?? '') === $entity_type && ($entry['entity_id'] ?? '') === $entity_id) {
        return;
      }
    }
    $entries[] = [
      'entity_type' => $entity_type,
      'entity_id' => $entity_id,
      'reason' => $reason,
    ];
    $config->set('locked_entities', $entries)->save();
  }

  /**
   * Removes an entity from the locked list.
   *
   * If the entry does not exist this is a no-op.
   *
   * @param string $entity_type
   *   The entity type machine name.
   * @param string $entity_id
   *   The entity ID as a string.
   */
  public function unlockEntity(string $entity_type, string $entity_id): void {
    $config = $this->configFactory->getEditable('entity_lock.settings');
    /** @var array<int, array<string, string>> $entries */
    $entries = $config->get('locked_entities') ?? [];
    $filtered = [];
    foreach ($entries as $entry) {
      if (($entry['entity_type'] ?? '') !== $entity_type || ($entry['entity_id'] ?? '') !== $entity_id) {
        $filtered[] = $entry;
      }
    }
    $config->set('locked_entities', $filtered)->save();
  }

}
