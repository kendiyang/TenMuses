import * as React from "react"

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onCheckedChange?: (checked: boolean) => void
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, onCheckedChange, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onCheckedChange?.(e.target.checked)
      props.onChange?.(e)
    }

    return (
      <input
        type="checkbox"
        ref={ref}
        className={`h-4 w-4 rounded border border-gray-300 text-primary focus:ring-2 focus:ring-offset-2 focus:ring-primary ${
          className || ''
        }`}
        onChange={handleChange}
        {...props}
      />
    )
  }
)

Checkbox.displayName = "Checkbox"

export { Checkbox }
