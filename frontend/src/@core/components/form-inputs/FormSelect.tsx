'use client';
import { Box, FormLabel, MenuItem, TextField } from '@mui/material';
import { Controller, type Control, type FieldPath, type FieldValues } from 'react-hook-form';
type Props<T extends FieldValues> = {
  control: Control<T>;
  name: FieldPath<T>;
  label: string;
  placeholder?: string;
  options: { label: string; value: string | number }[];
  disabled?: boolean;
};
export default function FormSelect<T extends FieldValues>({
  control,
  name,
  label,
  placeholder,
  options,
  disabled,
}: Props<T>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => (
        <Box className="form-field">
          <FormLabel>
            {label} <span>*</span>
          </FormLabel>
          <TextField
            {...field}
            select
            fullWidth
            disabled={disabled}
            value={field.value ?? ''}
            error={!!fieldState.error}
            helperText={fieldState.error?.message}
            slotProps={{ select: { displayEmpty: true } }}
          >
            {placeholder && (
              <MenuItem value="" disabled>
                {placeholder}
              </MenuItem>
            )}
            {options.map((o) => (
              <MenuItem key={o.value} value={o.value}>
                {o.label}
              </MenuItem>
            ))}
          </TextField>
        </Box>
      )}
    />
  );
}
