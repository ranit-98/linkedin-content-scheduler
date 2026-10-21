'use client';
import { Box, FormLabel, TextField, type TextFieldProps } from '@mui/material';
import { Controller, type Control, type FieldPath, type FieldValues } from 'react-hook-form';
type Props<T extends FieldValues> = Omit<
  TextFieldProps,
  'name' | 'value' | 'onChange' | 'error' | 'helperText' | 'label'
> & { control: Control<T>; name: FieldPath<T>; label: string };
export default function FormInputField<T extends FieldValues>({
  control,
  name,
  label,
  ...props
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
            {...props}
            {...field}
            value={field.value ?? ''}
            error={!!fieldState.error}
            helperText={fieldState.error?.message}
            fullWidth
          />
        </Box>
      )}
    />
  );
}
