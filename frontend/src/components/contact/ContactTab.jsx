import React, { useState } from 'react';
import axios from 'axios';
import { Mail } from 'lucide-react';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { toast } from '../../hooks/use-toast';
import { formatApiErrorDetail } from '../../context/AuthContext';
import { pick } from '../../i18n/lang';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function ContactTab({ language = 'fr' }) {
  const [form, setForm] = useState({ name: '', email: '', message: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/contact`, form);
      toast({
        title: pick(language, 'Message envoyé', 'Message sent', 'تم إرسال الرسالة'),
        description: pick(language, 'Nous vous répondrons dans les plus brefs délais.', "We'll get back to you shortly.", 'سنرد عليك في أقرب وقت ممكن.'),
      });
      setForm({ name: '', email: '', message: '' });
    } catch (err) {
      toast({
        title: pick(language, 'Échec de l\'envoi', 'Send failed', 'فشل الإرسال'),
        // undefined → libellé par défaut (français) de formatApiErrorDetail.
        description: formatApiErrorDetail(err.response?.data?.detail, pick(language, undefined, undefined, 'حدث خطأ. يرجى إعادة المحاولة.')),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="afcfta-card" style={{ maxWidth: 560 }}>
      <form className="space-y-4" onSubmit={handleSubmit} data-testid="contact-form">
        <div className="space-y-1">
          <Label htmlFor="contact-name">{pick(language, 'Nom', 'Name', 'الاسم')}</Label>
          <Input
            id="contact-name"
            required
            maxLength={100}
            data-testid="contact-name-input"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="contact-email">{pick(language, 'Email', 'Email', 'البريد الإلكتروني')}</Label>
          <Input
            id="contact-email"
            type="email"
            required
            data-testid="contact-email-input"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="contact-message">{pick(language, 'Message', 'Message', 'الرسالة')}</Label>
          <Textarea
            id="contact-message"
            rows={6}
            required
            maxLength={5000}
            data-testid="contact-message-input"
            value={form.message}
            onChange={(e) => setForm({ ...form, message: e.target.value })}
          />
        </div>
        <Button type="submit" disabled={loading} data-testid="contact-submit-btn">
          <Mail size={15} style={{ marginRight: 6 }} />
          {loading ? (pick(language, 'Envoi…', 'Sending…', 'جارٍ الإرسال…')) : pick(language, 'Envoyer', 'Send', 'إرسال')}
        </Button>
      </form>
    </div>
  );
}
