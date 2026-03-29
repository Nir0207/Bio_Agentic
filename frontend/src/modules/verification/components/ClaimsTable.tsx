import { Chip, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';

import type { ClaimResult } from '../../../types/verification';
import { pct, titleCase } from '../../../utils/format';

interface ClaimsTableProps {
  claims: ClaimResult[];
}

const statusColorMap: Record<string, 'success' | 'warning' | 'error'> = {
  supported: 'success',
  partially_supported: 'warning',
  unsupported: 'error',
};

export function ClaimsTable({ claims }: ClaimsTableProps) {
  return (
    <Table size='small'>
      <TableHead>
        <TableRow>
          <TableCell>Claim</TableCell>
          <TableCell>Status</TableCell>
          <TableCell>Confidence</TableCell>
          <TableCell>Citations</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {claims.map((claim, index) => (
          <TableRow key={`${claim.claim}-${index}`}>
            <TableCell>{claim.claim}</TableCell>
            <TableCell>
              <Chip
                size='small'
                label={titleCase(claim.status)}
                color={statusColorMap[claim.status] || 'warning'}
              />
            </TableCell>
            <TableCell>{pct(claim.confidence)}</TableCell>
            <TableCell>{claim.citations.length}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
