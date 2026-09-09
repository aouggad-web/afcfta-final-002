import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import KenyaRemissionAuthorization from './KenyaRemissionAuthorization';


describe('KenyaRemissionAuthorization', () => {
  it('defaults to an unknown eligibility choice', () => {
    render(<KenyaRemissionAuthorization />);
    expect(screen.getByLabelText('Je ne sais pas')).toBeChecked();
    expect(screen.queryByTestId('kenya-authorization-details')).not.toBeInTheDocument();
  });

  it('asks for reference, period and authorized goods after yes', async () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <KenyaRemissionAuthorization value={{ answer: 'unknown' }} onChange={onChange} />,
    );
    await userEvent.click(screen.getByLabelText('Oui'));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ answer: 'yes' }));
    rerender(<KenyaRemissionAuthorization value={{ answer: 'yes' }} onChange={onChange} />);
    expect(screen.getByTestId('kenya-authorization-details')).toBeInTheDocument();
    expect(screen.getByText(/Lignes tarifaires exactes autorisées/)).toBeInTheDocument();
  });

  it('records a negative answer without requesting authorization details', async () => {
    const onChange = vi.fn();
    render(<KenyaRemissionAuthorization value={{ answer: 'unknown' }} onChange={onChange} />);
    await userEvent.click(screen.getByLabelText('Non'));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ answer: 'no' }));
    expect(screen.queryByTestId('kenya-authorization-details')).not.toBeInTheDocument();
  });
});
