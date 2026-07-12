import { XIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

import type { KeyValuePair } from '@/features/endpoints/api'

interface KeyValueListEditorProps {
  label: string
  items: KeyValuePair[]
  onChange: (items: KeyValuePair[]) => void
}

export function KeyValueListEditor({ label, items, onChange }: KeyValueListEditorProps) {
  const addRow = () => onChange([...items, { key: '', value: '', description: '' }])

  const updateRow = (index: number, patch: Partial<KeyValuePair>) =>
    onChange(items.map((item, i) => (i === index ? { ...item, ...patch } : item)))

  const removeRow = (index: number) => onChange(items.filter((_, i) => i !== index))

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>{label}</Label>
        <Button type="button" variant="outline" size="sm" onClick={addRow}>
          Adicionar
        </Button>
      </div>
      {items.length === 0 && <p className="text-sm text-muted-foreground">Nenhum item.</p>}
      {items.map((item, index) => (
        <div key={index} className="flex gap-2">
          <Input
            placeholder="Chave"
            value={item.key}
            onChange={(e) => updateRow(index, { key: e.target.value })}
          />
          <Input
            placeholder="Valor"
            value={item.value}
            onChange={(e) => updateRow(index, { value: e.target.value })}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => removeRow(index)}
            aria-label="Remover"
          >
            <XIcon />
          </Button>
        </div>
      ))}
    </div>
  )
}
