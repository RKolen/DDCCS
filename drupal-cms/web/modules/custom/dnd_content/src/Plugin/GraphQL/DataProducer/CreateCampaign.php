<?php

declare(strict_types=1);

namespace Drupal\dnd_content\Plugin\GraphQL\DataProducer;

use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\Plugin\Context\ContextDefinition;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Drupal\graphql\Attribute\DataProducer;
use Drupal\graphql\GraphQL\Execution\FieldContext;
use Drupal\graphql\Plugin\GraphQL\DataProducer\DataProducerPluginBase;
use Drupal\taxonomy\Entity\Term;
use GraphQL\Error\UserError;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Creates a new campaign taxonomy term.
 */
#[DataProducer(
  id: "create_campaign",
  name: new TranslatableMarkup("Create Campaign"),
  description: new TranslatableMarkup("Creates a new campaign taxonomy term."),
  produces: new ContextDefinition(
    data_type: "any",
    label: new TranslatableMarkup("Campaign term"),
  ),
  consumes: [
    "name" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Campaign name"),
    ),
    "status" => new ContextDefinition(
      data_type: "string",
      label: new TranslatableMarkup("Campaign status"),
      required: FALSE,
    ),
  ],
)]
final class CreateCampaign extends DataProducerPluginBase implements ContainerFactoryPluginInterface {

  /**
   * The current user.
   *
   * @var \Drupal\Core\Session\AccountInterface
   */
  protected AccountInterface $currentUser;

  /**
   * {@inheritdoc}
   *
   * @param \Symfony\Component\DependencyInjection\ContainerInterface $container
   *   The service container.
   * @param array<string, mixed> $configuration
   *   Plugin configuration.
   * @param string $plugin_id
   *   The plugin ID.
   * @param mixed $plugin_definition
   *   The plugin definition.
   */
  public static function create(
    ContainerInterface $container,
    array $configuration,
    $plugin_id,
    $plugin_definition,
  ): self {
    $instance = new self($configuration, $plugin_id, $plugin_definition);
    $instance->currentUser = $container->get('current_user');
    return $instance;
  }

  /**
   * Resolves the mutation by creating a campaign taxonomy term.
   *
   * @param string $name
   *   The campaign name.
   * @param string|null $status
   *   The optional lifecycle status value.
   * @param \Drupal\graphql\GraphQL\Execution\FieldContext $context
   *   The GraphQL field execution context.
   *
   * @return \Drupal\taxonomy\Entity\Term
   *   The newly created term.
   *
   * @throws \GraphQL\Error\UserError
   *   When the user lacks permission or the term fails validation.
   */
  public function resolve(string $name, ?string $status, FieldContext $context): Term {
    $values = [
      'vid'  => 'campaign',
      'name' => trim($name),
    ];

    if ($status !== NULL && $status !== '') {
      $values['field_campaign_status'] = $status;
    }

    $term = Term::create($values);

    if (!$term->access('create', $this->currentUser)) {
      $context->addCacheableDependency($this->currentUser);
      throw new UserError('You do not have permission to create campaigns.');
    }

    $violations = $term->validate();
    if ($violations->count() > 0) {
      throw new UserError((string) $violations->get(0)->getMessage());
    }

    $term->save();

    return $term;
  }

}
