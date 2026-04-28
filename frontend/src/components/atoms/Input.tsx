import React from 'react';
import * as styles from './Input.module.css';

interface InputProps {
  id?: string;
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  type?: 'text' | 'search' | 'email' | 'password' | 'number';
  disabled?: boolean;
  error?: string;
  autoFocus?: boolean;
  className?: string;
}

export function Input({
  id,
  label,
  placeholder,
  value,
  onChange,
  type = 'text',
  disabled = false,
  error,
  autoFocus = false,
  className,
}: InputProps): React.ReactElement {
  const inputClass = [
    styles.input,
    error ? styles.hasError : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div className={styles.wrapper}>
      {label && (
        <label htmlFor={id} className={styles.label}>{label}</label>
      )}
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        autoFocus={autoFocus}
        className={inputClass}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={error && id ? `${id}-error` : undefined}
      />
      {error && (
        <span
          id={id ? `${id}-error` : undefined}
          className={styles.errorMsg}
          role="alert"
        >
          {error}
        </span>
      )}
    </div>
  );
}

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  id?: string;
  label?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  options: SelectOption[];
  disabled?: boolean;
  className?: string;
}

export function Select({
  id,
  label,
  value,
  onChange,
  options,
  disabled = false,
  className,
}: SelectProps): React.ReactElement {
  return (
    <div className={styles.wrapper}>
      {label && (
        <label htmlFor={id} className={styles.label}>{label}</label>
      )}
      <select
        id={id}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={`${styles.select}${className ? ` ${className}` : ''}`}
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}
