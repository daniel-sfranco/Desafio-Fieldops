import { test, expect } from '@playwright/test';

test('Fluxo completo: Login -> Criar OS -> Transição de Status', async ({ page }) => {
  // Gerador de título único com timestamp para evitar conflito caso o teste rode múltiplas vezes
  const uniqueTitle = `Manutenção no Ar Condicionado #${Date.now()}`;
  const description = 'Manutenção básica preventiva no Ar Condicionado';

  // Login
  await page.goto('/');
  await page.locator('input[type="email"]').fill('supervisor-a@fieldops.eval');
  await page.locator('input[type="password"]').fill('password123');
  await page.getByRole('button', { name: 'Entrar' }).click();
  await expect(page.getByText('Ordens de Serviço')).toBeVisible();

  // Criação da ordem de serviço
  await page.getByRole('button', { name: 'Nova Ordem de Serviço'}).click();
  await page.locator('.form-group')
    .filter({ hasText: 'Título da OS' })
    .locator('input')
    .fill(uniqueTitle);
  await page.locator('.form-group')
    .filter({ hasText: 'Descrição detalhada' })
    .locator('textarea')
    .fill(description);
  await page.locator('.form-group')
    .filter({ hasText: 'Prioridade' })
    .locator('select')
    .selectOption('low');
  await page.getByRole('button', { name: 'Criar Ordem de Serviço'}).click();

  await expect(page.getByText(uniqueTitle)).toBeVisible();
  await expect(page.getByText(description).first()).toBeVisible();

  // Validação do fluxo
  // Mudar para 'em andamento'
  await page.locator('.card')
    .filter({ hasText: uniqueTitle })
    .getByRole('button', { name: 'Detalhes / Alterar' })
    .click();

  await page.locator('.form-group')
    .filter({ hasText: 'Status' })
    .locator('select')
    .selectOption('in_progress');

  await page.locator('.form-group')
    .filter({ hasText: 'Técnico Designado (ID do Técnico)' })
    .locator('input')
    .fill('1');

  await page.getByRole('button', { name: 'Aplicar alterações' }).click();

  await expect(
    page.locator('.card').filter({ hasText: uniqueTitle })
  ).toContainText('Em Andamento');

  // Mudar para 'concluído'
  await page.locator('.card')
    .filter({ hasText: uniqueTitle })
    .getByRole('button', { name: 'Detalhes / Alterar' })
    .click();

  // Marcar item do checklist
  await page.getByText('Verificação inicial').click();

  await page.locator('.form-group')
    .filter({ hasText: 'Status' })
    .locator('select')
    .selectOption('done');

  // Preencher notas de resolução obrigatórias (mín. 10 caracteres)
  await page.locator('.form-group')
    .filter({ hasText: 'Notas de Resolução' })
    .locator('textarea')
    .fill('Manutenção preventiva do ar condicionado finalizada com sucesso.');

  await page.getByRole('button', { name: 'Aplicar alterações' }).click();

  await expect(
    page.locator('.card').filter({ hasText: uniqueTitle })
  ).toContainText('Concluída');
});