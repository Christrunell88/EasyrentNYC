import React from 'react';
import { Link } from 'react-router-dom';
import { Building2, MapPin, Mail, Phone, Facebook, Twitter, Instagram, Linkedin } from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  // Internal links for SEO - organized by category
  const locationLinks = [
    { name: 'Manhattan', path: '/location/manhattan' },
    { name: 'Brooklyn', path: '/location/brooklyn' },
    { name: 'Queens', path: '/location/queens' },
    { name: 'Bronx', path: '/location/bronx' },
    { name: 'Jersey City', path: '/location/jersey-city' },
    { name: 'Hoboken', path: '/location/hoboken' },
  ];

  const neighborhoodLinks = [
    { name: 'Williamsburg', path: '/location/williamsburg' },
    { name: 'Long Island City', path: '/location/long-island-city' },
    { name: 'Weehawken', path: '/location/weehawken' },
    { name: 'Harrison', path: '/location/harrison' },
  ];

  const resourceLinks = [
    { name: 'Blog', path: '/blog' },
    { name: 'FAQ', path: '/faq' },
    { name: 'No Fee Apartment Guide', path: '/blog/guide-to-no-fee-apartments' },
    { name: 'Best Neighborhoods', path: '/blog/best-neighborhoods' },
    { name: 'Apartment Checklist', path: '/blog/apartment-checklist' },
  ];

  const companyLinks = [
    { name: 'Browse Apartments', path: '/dashboard' },
    { name: '#FeeFreeFinds', path: '/fee-free-finds' },
    { name: 'All Locations', path: '/neighborhoods' },
  ];

  const socialLinks = [
    { name: 'Facebook', icon: Facebook, url: 'https://facebook.com/NoFeesApts' },
    { name: 'Twitter', icon: Twitter, url: 'https://twitter.com/NoFeesApts' },
    { name: 'Instagram', icon: Instagram, url: 'https://instagram.com/NoFeesApts' },
    { name: 'LinkedIn', icon: Linkedin, url: 'https://linkedin.com/company/nofeesapts' },
  ];

  return (
    <footer className="bg-[#0a0a0a] border-t border-[#D4AF37]/20">
      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
          {/* Brand Column */}
          <div className="col-span-2 md:col-span-4 lg:col-span-1">
            <Link to="/" className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#D4AF37] to-[#B8963E] flex items-center justify-center">
                <Building2 className="w-6 h-6 text-[#0a0a0a]" />
              </div>
              <span className="text-xl font-bold text-[#D4AF37] font-philosopher">NoFeesApts</span>
            </Link>
            <p className="text-[#888] text-sm mb-4">
              NYC's premier platform for finding no broker fee apartments. Save thousands on your next rental.
            </p>
            {/* Social Links */}
            <div className="flex gap-3">
              {socialLinks.map((social) => (
                <a
                  key={social.name}
                  href={social.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-9 h-9 rounded-full bg-[#1a1a1a] border border-[#333] flex items-center justify-center text-[#888] hover:text-[#D4AF37] hover:border-[#D4AF37]/50 transition-all"
                  aria-label={social.name}
                >
                  <social.icon className="w-4 h-4" />
                </a>
              ))}
            </div>
          </div>

          {/* Locations Column */}
          <div>
            <h3 className="text-[#F5F5F5] font-semibold mb-4 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#D4AF37]" />
              Locations
            </h3>
            <ul className="space-y-2">
              {locationLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.path}
                    className="text-[#888] hover:text-[#D4AF37] text-sm transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Neighborhoods Column */}
          <div>
            <h3 className="text-[#F5F5F5] font-semibold mb-4">Neighborhoods</h3>
            <ul className="space-y-2">
              {neighborhoodLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.path}
                    className="text-[#888] hover:text-[#D4AF37] text-sm transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
              <li>
                <Link
                  to="/neighborhoods"
                  className="text-[#D4AF37] hover:text-[#E5C158] text-sm font-medium transition-colors"
                >
                  View All →
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources Column */}
          <div>
            <h3 className="text-[#F5F5F5] font-semibold mb-4">Resources</h3>
            <ul className="space-y-2">
              {resourceLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.path}
                    className="text-[#888] hover:text-[#D4AF37] text-sm transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Column */}
          <div>
            <h3 className="text-[#F5F5F5] font-semibold mb-4">Company</h3>
            <ul className="space-y-2">
              {companyLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.path}
                    className="text-[#888] hover:text-[#D4AF37] text-sm transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
            {/* Contact Info */}
            <div className="mt-4 pt-4 border-t border-[#333]">
              <a
                href="mailto:hello@nofeesapts.com"
                className="flex items-center gap-2 text-[#888] hover:text-[#D4AF37] text-sm mb-2"
              >
                <Mail className="w-4 h-4" />
                hello@nofeesapts.com
              </a>
              <a
                href="tel:+16465550123"
                className="flex items-center gap-2 text-[#888] hover:text-[#D4AF37] text-sm"
              >
                <Phone className="w-4 h-4" />
                (646) 555-0123
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-[#1a1a1a]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-[#666] text-sm">
              © {currentYear} NoFeesApts.com. All rights reserved.
            </p>
            <div className="flex gap-6">
              <Link to="/privacy" className="text-[#666] hover:text-[#888] text-sm">Privacy Policy</Link>
              <Link to="/terms" className="text-[#666] hover:text-[#888] text-sm">Terms of Service</Link>
              <Link to="/sitemap" className="text-[#666] hover:text-[#888] text-sm">Sitemap</Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
