import React from 'react';
import { Input } from '../atoms/Input';
import { Button } from '../atoms/Button';
import * as styles from './SearchBar.module.css';

interface SearchBarProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  loading?: boolean;
  placeholder?: string;
}

export function SearchBar({
  value,
  onChange,
  onSubmit,
  loading = false,
  placeholder = 'Search characters, spells, items, monsters...',
}: SearchBarProps): React.ReactElement {
  return (
    <form className={styles.form} onSubmit={onSubmit}>
      <div className={styles.inputWrapper}>
        <Input
          type="search"
          placeholder={placeholder}
          value={value}
          onChange={onChange}
        />
      </div>
      <Button
        type="submit"
        variant="primary"
        size="md"
        icon="crystal-ball"
        loading={loading}
      >
        {loading ? 'Searching...' : 'Search'}
      </Button>
    </form>
  );
}
