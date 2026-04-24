<?php

declare(strict_types=1);

namespace Drupal\entity_lock\Form;

use Drupal\Component\Plugin\Exception\PluginNotFoundException;
use Drupal\Core\Config\ConfigFactoryInterface;
use Drupal\Core\Config\TypedConfigManagerInterface;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Form\ConfigFormBase;
use Drupal\Core\Form\FormStateInterface;
use Drupal\entity_lock\EntityLockManager;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Configuration form for the Entity Lock module.
 *
 * Provides a table of currently locked entities with per-row Remove actions,
 * and a form section to add new entity locks.
 */
final class EntityLockSettingsForm extends ConfigFormBase {

  /**
   * The entity type manager.
   *
   * @var \Drupal\Core\Entity\EntityTypeManagerInterface
   */
  protected EntityTypeManagerInterface $entityTypeManager;

  /**
   * The entity lock manager service.
   *
   * @var \Drupal\entity_lock\EntityLockManager
   */
  protected EntityLockManager $lockManager;

  /**
   * Constructs an EntityLockSettingsForm.
   *
   * @param \Drupal\Core\Config\ConfigFactoryInterface $config_factory
   *   The config factory.
   * @param \Drupal\Core\Config\TypedConfigManagerInterface $typed_config_manager
   *   The typed config manager.
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entity_type_manager
   *   The entity type manager.
   * @param \Drupal\entity_lock\EntityLockManager $lock_manager
   *   The entity lock manager.
   */
  public function __construct(
    ConfigFactoryInterface $config_factory,
    TypedConfigManagerInterface $typed_config_manager,
    EntityTypeManagerInterface $entity_type_manager,
    EntityLockManager $lock_manager,
  ) {
    parent::__construct($config_factory, $typed_config_manager);
    $this->entityTypeManager = $entity_type_manager;
    $this->lockManager = $lock_manager;
  }

  /**
   * {@inheritdoc}
   */
  public static function create(ContainerInterface $container): static {
    return new static(
      $container->get('config.factory'),
      $container->get('config.typed'),
      $container->get('entity_type.manager'),
      $container->get('entity_lock.manager'),
    );
  }

  /**
   * {@inheritdoc}
   */
  public function getFormId(): string {
    return 'entity_lock_settings_form';
  }

  /**
   * {@inheritdoc}
   *
   * @return list<string>
   *   The config names this form manages.
   */
  protected function getEditableConfigNames(): array {
    return ['entity_lock.settings'];
  }

  /**
   * {@inheritdoc}
   *
   * @param array<string, mixed> $form
   *   The form render array.
   * @param \Drupal\Core\Form\FormStateInterface $form_state
   *   The form state.
   *
   * @return array<string, mixed>
   *   The completed form render array.
   */
  public function buildForm(array $form, FormStateInterface $form_state): array {
    $locked_entities = $this->lockManager->getLockedEntities();

    $form['locked_entities_section'] = [
      '#type' => 'details',
      '#title' => $this->t('Currently locked entities'),
      '#open' => TRUE,
    ];

    $form['locked_entities_section']['table'] = [
      '#type' => 'table',
      '#header' => [
        $this->t('Entity type'),
        $this->t('Entity ID'),
        $this->t('Label'),
        $this->t('Reason'),
        $this->t('Actions'),
      ],
      '#empty' => $this->t('No entities are currently locked.'),
    ];

    foreach ($locked_entities as $delta => $entry) {
      $entity_type_id = $entry['entity_type'] ?? '';
      $entity_id = $entry['entity_id'] ?? '';
      $reason = $entry['reason'] ?? '';

      $form['locked_entities_section']['table'][$delta]['entity_type'] = [
        '#markup' => $this->resolveEntityTypeLabel($entity_type_id),
      ];
      $form['locked_entities_section']['table'][$delta]['entity_id'] = [
        '#markup' => $entity_id,
      ];
      $form['locked_entities_section']['table'][$delta]['label'] = [
        '#markup' => $this->resolveEntityLabel($entity_type_id, $entity_id),
      ];
      $form['locked_entities_section']['table'][$delta]['reason'] = [
        '#markup' => $reason !== '' ? $reason : (string) $this->t('(none)'),
      ];
      $form['locked_entities_section']['table'][$delta]['actions'] = [
        '#type' => 'submit',
        '#value' => $this->t('Remove'),
        '#name' => 'remove_' . $delta,
        '#submit' => ['::removeEntityLock'],
        '#limit_validation_errors' => [],
        '#entity_type_to_remove' => $entity_type_id,
        '#entity_id_to_remove' => $entity_id,
      ];
    }

    $form['add_lock'] = [
      '#type' => 'details',
      '#title' => $this->t('Add a new entity lock'),
      '#open' => TRUE,
    ];

    $form['add_lock']['entity_type'] = [
      '#type' => 'select',
      '#title' => $this->t('Entity type'),
      '#options' => $this->getEntityTypeOptions(),
      '#required' => TRUE,
      '#description' => $this->t('Select the entity type to lock.'),
    ];

    $form['add_lock']['entity_id'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Entity ID'),
      '#required' => TRUE,
      '#description' => $this->t('The numeric or string ID of the entity to lock.'),
      '#size' => 20,
    ];

    $form['add_lock']['reason'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Reason'),
      '#required' => FALSE,
      '#description' => $this->t('Optional. Shown to users who attempt to delete this entity.'),
      '#maxlength' => 255,
    ];

    $form['add_lock']['add_entity_lock'] = [
      '#type' => 'submit',
      '#value' => $this->t('Add lock'),
      '#name' => 'add_entity_lock',
      '#submit' => ['::addEntityLock'],
    ];

    return $form;
  }

  /**
   * Submit handler: adds a new entity lock entry.
   *
   * @param array<string, mixed> $form
   *   The form render array.
   * @param \Drupal\Core\Form\FormStateInterface $form_state
   *   The form state.
   */
  public function addEntityLock(array &$form, FormStateInterface $form_state): void {
    $entity_type = (string) $form_state->getValue('entity_type');
    $entity_id = trim((string) $form_state->getValue('entity_id'));
    $reason = trim((string) $form_state->getValue('reason'));

    $this->lockManager->lockEntity($entity_type, $entity_id, $reason);
    $this->messenger()->addStatus($this->t('The entity lock has been added.'));
    $form_state->setRebuild();
  }

  /**
   * Submit handler: removes an existing entity lock entry.
   *
   * @param array<string, mixed> $form
   *   The form render array.
   * @param \Drupal\Core\Form\FormStateInterface $form_state
   *   The form state.
   */
  public function removeEntityLock(array &$form, FormStateInterface $form_state): void {
    $triggering = $form_state->getTriggeringElement();
    $entity_type = (string) ($triggering['#entity_type_to_remove'] ?? '');
    $entity_id = (string) ($triggering['#entity_id_to_remove'] ?? '');

    if ($entity_type !== '' && $entity_id !== '') {
      $this->lockManager->unlockEntity($entity_type, $entity_id);
      $this->messenger()->addStatus($this->t('The entity lock has been removed.'));
    }

    $form_state->setRebuild();
  }

  /**
   * {@inheritdoc}
   *
   * Validation is scoped to the "Add lock" action only; Remove buttons bypass
   * validation via #limit_validation_errors = [].
   *
   * @param array<array-key, mixed> $form
   *   The form render array.
   */
  public function validateForm(array &$form, FormStateInterface $form_state): void {
    parent::validateForm($form, $form_state);

    $triggering = $form_state->getTriggeringElement();
    if (($triggering['#name'] ?? '') !== 'add_entity_lock') {
      return;
    }

    $entity_id = trim((string) $form_state->getValue('entity_id'));
    if ($entity_id === '') {
      $form_state->setErrorByName('entity_id', $this->t('Entity ID cannot be empty.'));
    }
  }

  /**
   * {@inheritdoc}
   *
   * All form actions are handled by dedicated per-action submit handlers.
   * This method is required by ConfigFormBase but has no action to perform.
   *
   * @param array<array-key, mixed> $form
   *   The form render array.
   */
  public function submitForm(array &$form, FormStateInterface $form_state): void {}

  /**
   * Returns a sorted list of entity type options for the select element.
   *
   * @return array<string, string>
   *   Associative array keyed by entity type machine name with human-readable
   *   label values, sorted alphabetically by label.
   */
  protected function getEntityTypeOptions(): array {
    $definitions = $this->entityTypeManager->getDefinitions();
    $options = [];
    foreach ($definitions as $id => $definition) {
      $options[$id] = (string) $definition->getLabel();
    }
    asort($options);
    return $options;
  }

  /**
   * Resolves the human-readable label for an entity type machine name.
   *
   * @param string $entity_type_id
   *   The entity type machine name.
   *
   * @return string
   *   The human-readable entity type label, or the machine name if not found.
   */
  protected function resolveEntityTypeLabel(string $entity_type_id): string {
    if ($entity_type_id === '') {
      return (string) $this->t('(unknown)');
    }
    try {
      $definition = $this->entityTypeManager->getDefinition($entity_type_id);
      return (string) $definition->getLabel();
    }
    catch (PluginNotFoundException $e) {
      return $entity_type_id;
    }
  }

  /**
   * Attempts to load the human-readable label of a specific entity.
   *
   * @param string $entity_type_id
   *   The entity type machine name.
   * @param string $entity_id
   *   The entity ID.
   *
   * @return string
   *   The entity label, or a fallback string if the entity cannot be loaded.
   */
  protected function resolveEntityLabel(string $entity_type_id, string $entity_id): string {
    if ($entity_type_id === '' || $entity_id === '') {
      return (string) $this->t('(not found)');
    }
    try {
      $entity = $this->entityTypeManager->getStorage($entity_type_id)->load($entity_id);
      if ($entity === NULL) {
        return (string) $this->t('(not found)');
      }
      return $entity->label() ?? (string) $this->t('(no label)');
    }
    catch (PluginNotFoundException $e) {
      return (string) $this->t('(invalid entity type)');
    }
  }

}
