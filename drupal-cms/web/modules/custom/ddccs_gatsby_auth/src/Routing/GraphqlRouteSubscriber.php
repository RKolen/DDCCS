<?php

declare(strict_types=1);

namespace Drupal\ddccs_gatsby_auth\Routing;

use Drupal\Core\Routing\RouteSubscriberBase;
use Symfony\Component\Routing\RouteCollection;

/**
 * Adds Gatsby bearer token authentication to the GraphQL endpoint.
 */
final class GraphqlRouteSubscriber extends RouteSubscriberBase {

  private const GRAPHQL_ROUTE = 'graphql.query.graphql_compose_server';
  private const AUTH_PROVIDER = 'ddccs_gatsby_token';

  /**
   * {@inheritdoc}
   */
  protected function alterRoutes(RouteCollection $collection): void {
    $route = $collection->get(self::GRAPHQL_ROUTE);
    if ($route === NULL) {
      return;
    }

    $authProviders = $route->getOption('_auth') ?? [];
    if (!is_array($authProviders)) {
      $authProviders = [$authProviders];
    }

    if (!in_array(self::AUTH_PROVIDER, $authProviders, TRUE)) {
      array_unshift($authProviders, self::AUTH_PROVIDER);
    }

    $route->setOption('_auth', $authProviders);
  }

}
