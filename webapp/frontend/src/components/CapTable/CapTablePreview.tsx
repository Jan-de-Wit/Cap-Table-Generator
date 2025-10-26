/**
 * CapTablePreview Component
 * Main preview of cap table with collapsible sections
 */

import { useState } from 'react';
import { ChevronDown, ChevronRight, Building2, Users, FileText, TrendingUp, DollarSign, Target } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import type { SecurityClass, Holder, Instrument, Round } from '../../types/captable.types';

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function Section({ title, icon, children, defaultOpen = true }: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 p-4 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        {isOpen ? <ChevronDown className="w-5 h-5 text-gray-600" /> : <ChevronRight className="w-5 h-5 text-gray-600" />}
        {icon}
        <span className="font-semibold text-gray-900">{title}</span>
      </button>
      {isOpen && (
        <div className="p-4 bg-white">
          {children}
        </div>
      )}
    </div>
  );
}

export function CapTablePreview() {
  const { capTable, metrics } = useAppStore();
  
  if (!capTable) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p>No cap table data yet</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full overflow-y-auto p-6 space-y-4 bg-gray-50">
      {/* Company Info */}
      <Section title="Company Information" icon={<Building2 className="w-5 h-5 text-blue-600" />}>
        <div className="space-y-2">
          <div>
            <span className="text-sm font-medium text-gray-600">Name:</span>
            <span className="ml-2 text-sm text-gray-900">{capTable.company.name}</span>
          </div>
          {capTable.company.incorporation_date && (
            <div>
              <span className="text-sm font-medium text-gray-600">Incorporated:</span>
              <span className="ml-2 text-sm text-gray-900">{capTable.company.incorporation_date}</span>
            </div>
          )}
          {capTable.company.current_pps && (
            <div>
              <span className="text-sm font-medium text-gray-600">Current PPS:</span>
              <span className="ml-2 text-sm text-gray-900">${capTable.company.current_pps.toFixed(2)}</span>
            </div>
          )}
        </div>
      </Section>
      
      {/* Securities/Classes */}
      <Section title="Security Classes" icon={<FileText className="w-5 h-5 text-purple-600" />}>
        {capTable.classes.length === 0 ? (
          <p className="text-sm text-gray-500">No security classes defined</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-gray-600 font-medium">Name</th>
                  <th className="text-left py-2 text-gray-600 font-medium">Type</th>
                </tr>
              </thead>
              <tbody>
                {capTable.classes.map((cls: SecurityClass) => (
                  <tr key={cls.class_id} className="border-b last:border-b-0">
                    <td className="py-2 text-gray-900">{cls.name}</td>
                    <td className="py-2 text-gray-600">{cls.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
      
      {/* Holders */}
      <Section title="Holders" icon={<Users className="w-5 h-5 text-green-600" />}>
        {capTable.holders.length === 0 ? (
          <p className="text-sm text-gray-500">No holders defined</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-gray-600 font-medium">Name</th>
                  <th className="text-left py-2 text-gray-600 font-medium">Type</th>
                </tr>
              </thead>
              <tbody>
                {capTable.holders.map((holder: Holder) => (
                  <tr key={holder.holder_id} className="border-b last:border-b-0">
                    <td className="py-2 text-gray-900">{holder.name}</td>
                    <td className="py-2 text-gray-600">{holder.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
      
      {/* Instruments/Holdings */}
      <Section title="Instruments" icon={<DollarSign className="w-5 h-5 text-yellow-600" />}>
        {capTable.instruments.length === 0 ? (
          <p className="text-sm text-gray-500">No instruments defined</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-gray-600 font-medium">Holder</th>
                  <th className="text-left py-2 text-gray-600 font-medium">Class</th>
                  <th className="text-right py-2 text-gray-600 font-medium">Quantity</th>
                </tr>
              </thead>
              <tbody>
                {capTable.instruments.map((inst: Instrument) => {
                  const holder = capTable.holders.find(h => h.holder_id === inst.holder_id);
                  const secClass = capTable.classes.find(c => c.class_id === inst.class_id);
                  return (
                    <tr key={inst.instrument_id} className="border-b last:border-b-0">
                      <td className="py-2 text-gray-900">{holder?.name || 'Unknown'}</td>
                      <td className="py-2 text-gray-600">{secClass?.name || 'Unknown'}</td>
                      <td className="py-2 text-gray-900 text-right">{inst.initial_quantity.toLocaleString()}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Section>
      
      {/* Rounds */}
      {capTable.rounds && capTable.rounds.length > 0 && (
        <Section title="Financing Rounds" icon={<TrendingUp className="w-5 h-5 text-red-600" />}>
          <div className="space-y-3">
            {capTable.rounds.map((round: Round) => (
              <div key={round.round_id} className="p-3 bg-gray-50 rounded-lg">
                <div className="font-medium text-gray-900 mb-2">{round.name}</div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Date:</span>
                    <span className="ml-2 text-gray-900">{round.round_date}</span>
                  </div>
                  {round.investment_amount && (
                    <div>
                      <span className="text-gray-600">Investment:</span>
                      <span className="ml-2 text-gray-900">${round.investment_amount.toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
      
      {/* Ownership Summary */}
      <Section title="Ownership Summary" icon={<Target className="w-5 h-5 text-indigo-600" />}>
        {!metrics || metrics.ownership.length === 0 ? (
          <p className="text-sm text-gray-500">No ownership data</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-gray-600 font-medium">Holder</th>
                  <th className="text-right py-2 text-gray-600 font-medium">Shares</th>
                  <th className="text-right py-2 text-gray-600 font-medium">% Issued</th>
                  <th className="text-right py-2 text-gray-600 font-medium">% FD</th>
                </tr>
              </thead>
              <tbody>
                {metrics.ownership.map((owner, index) => (
                  <tr key={index} className="border-b last:border-b-0">
                    <td className="py-2 text-gray-900">{owner.holder_name}</td>
                    <td className="py-2 text-gray-900 text-right">{owner.shares_issued.toLocaleString()}</td>
                    <td className="py-2 text-gray-900 text-right">{owner.percent_issued.toFixed(2)}%</td>
                    <td className="py-2 text-gray-900 text-right">{owner.percent_fd.toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {metrics && (
          <div className="mt-4 pt-4 border-t space-y-2">
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-600">Total Issued:</span>
              <span className="text-gray-900">{metrics.totals.issued.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-600">Fully Diluted:</span>
              <span className="text-gray-900">{metrics.totals.fullyDiluted.toLocaleString()}</span>
            </div>
          </div>
        )}
      </Section>
      
      {/* Option Pool */}
      {metrics && metrics.pool.size > 0 && (
        <Section title="Option Pool" icon={<Target className="w-5 h-5 text-orange-600" />}>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-600">Pool Size:</span>
              <span className="text-gray-900">{metrics.pool.size.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-600">Granted:</span>
              <span className="text-gray-900">{metrics.pool.granted.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-600">Remaining:</span>
              <span className="text-gray-900 font-semibold">{metrics.pool.remaining.toLocaleString()}</span>
            </div>
          </div>
        </Section>
      )}
    </div>
  );
}

