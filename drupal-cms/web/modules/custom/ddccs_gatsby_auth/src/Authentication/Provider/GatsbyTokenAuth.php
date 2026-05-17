<?php

declare(strict_types=1);

namespace Drupal\ddccs_gatsby_auth\Authentication\Provider;

use Drupal\Core\Authentication\AuthenticationProviderInterface;
use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\Core\Session\AccountInterface;
use Drupal\user\UserInterface;
use Symfony\Component\HttpFoundation\Request;

/**
 * Authenticates Gatsby GraphQL requests with a shared bearer token.
 */
final class GatsbyTokenAuth implements AuthenticationProviderInterface {

  private const AUTH_PREFIX = 'Bearer ';
  private const DEFAULT_USERNAME = 'gatsby_user';
  private const TOKEN_ENV = 'DRUPAL_GRAPHQL_TOKEN';
  private const USER_ENV = 'DRUPAL_GRAPHQL_USER';

  /**
   * Constructs a Gatsby token authentication provider.
   *
   * @param \Drupal\Core\Entity\EntityTypeManagerInterface $entityTypeManager
   *   The entity type manager.
   */
  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager,
  ) {
  }

  /**
   * {@inheritdoc}
   */
  public function applies(Request $request): bool {
    $authorization = $request->headers->get('Authorization', '');
    return str_starts_with($authorization, self::AUTH_PREFIX);
  }

  /**
   * {@inheritdoc}
   */
  public function authenticate(Request $request): ?AccountInterface {
    $authorization = $request->headers->get('Authorization', '');
    $token = trim(substr($authorization, strlen(self::AUTH_PREFIX)));
    $expectedToken = $this->getEnvValue(self::TOKEN_ENV);

    if ($token === '' || $expectedToken === '') {
      return NULL;
    }

    if (!hash_equals($expectedToken, $token)) {
      return NULL;
    }

    $username = $this->getEnvValue(self::USER_ENV) ?: self::DEFAULT_USERNAME;
    $accounts = $this->entityTypeManager
      ->getStorage('user')
      ->loadByProperties([
        'name' => $username,
        'status' => 1,
      ]);

    $account = reset($accounts);
    if (!$account instanceof UserInterface) {
      return NULL;
    }

    return $account;
  }

  /**
   * Gets a trimmed environment value.
   *
   * @param string $name
   *   The environment variable name.
   *
   * @return string
   *   The trimmed value, or an empty string when unset.
   */
  private function getEnvValue(string $name): string {
    $value = getenv($name);
    if ($value === FALSE) {
      return '';
    }

    return trim($value);
  }

}
