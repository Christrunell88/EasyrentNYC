import { Helmet } from 'react-helmet-async';

const SEO = ({ 
  title, 
  description, 
  keywords,
  image,
  url,
  type = 'website',
  structuredData,
  article,
  noindex = false,
  breadcrumbs,
  faq,
  product
}) => {
  const siteName = 'NoFeesApts.com';
  const defaultDescription = 'Find your perfect no-fee apartment in NYC and Northern New Jersey. Browse 200+ verified listings with real photos. No broker fees ever.';
  const defaultImage = 'https://nofeesapts.com/og-image.jpg';
  const baseUrl = 'https://nofeesapts.com';

  const fullTitle = title ? `${title} | ${siteName}` : `${siteName} - No Broker Fee Apartments in NYC & NJ`;
  const metaDescription = description || defaultDescription;
  const metaImage = image || defaultImage;
  const canonicalUrl = url ? `${baseUrl}${url}` : baseUrl;

  // Generate BreadcrumbList schema
  const breadcrumbSchema = breadcrumbs ? {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": breadcrumbs.map((crumb, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "name": crumb.name,
      "item": crumb.url ? `${baseUrl}${crumb.url}` : undefined
    }))
  } : null;

  // Generate FAQ schema
  const faqSchema = faq ? {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": faq.map(item => ({
      "@type": "Question",
      "name": item.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": item.answer
      }
    }))
  } : null;

  // Generate Article schema
  const articleSchema = article ? {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": article.title,
    "description": article.excerpt,
    "image": article.image,
    "datePublished": article.publishedDate,
    "dateModified": article.modifiedDate || article.publishedDate,
    "author": {
      "@type": "Organization",
      "name": siteName
    },
    "publisher": {
      "@type": "Organization",
      "name": siteName,
      "logo": {
        "@type": "ImageObject",
        "url": `${baseUrl}/logo.png`
      }
    },
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": canonicalUrl
    }
  } : null;

  // Generate Product schema for listings
  const productSchema = product ? {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": product.name,
    "description": product.description,
    "image": product.image,
    "brand": {
      "@type": "Brand",
      "name": product.brand || "NoFeesApts"
    },
    "offers": {
      "@type": "Offer",
      "url": canonicalUrl,
      "price": product.price,
      "priceCurrency": "USD",
      "priceValidUntil": new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      "availability": product.available ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      "seller": {
        "@type": "Organization",
        "name": siteName
      }
    }
  } : null;

  // Organization schema (for site-wide)
  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "NoFeesApts.com",
    "url": baseUrl,
    "logo": `${baseUrl}/logo.png`,
    "description": "NYC's premier platform for finding no broker fee apartments",
    "sameAs": [
      "https://www.facebook.com/NoFeesApts",
      "https://twitter.com/NoFeesApts",
      "https://www.instagram.com/NoFeesApts"
    ],
    "contactPoint": {
      "@type": "ContactPoint",
      "telephone": "+1-646-555-0123",
      "contactType": "customer service",
      "areaServed": ["US-NY", "US-NJ", "US-PA"],
      "availableLanguage": "English"
    }
  };

  // WebSite schema with search action
  const websiteSchema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": siteName,
    "url": baseUrl,
    "description": defaultDescription,
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": `${baseUrl}/dashboard?search={search_term_string}`
      },
      "query-input": "required name=search_term_string"
    }
  };

  return (
    <Helmet>
      {/* Primary Meta Tags */}
      <title>{fullTitle}</title>
      <meta name="title" content={fullTitle} />
      <meta name="description" content={metaDescription} />
      {keywords && <meta name="keywords" content={keywords} />}
      <link rel="canonical" href={canonicalUrl} />
      {noindex && <meta name="robots" content="noindex, nofollow" />}

      {/* Open Graph / Facebook */}
      <meta property="og:type" content={type} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={metaDescription} />
      <meta property="og:image" content={metaImage} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:site_name" content={siteName} />
      <meta property="og:locale" content="en_US" />

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:url" content={canonicalUrl} />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={metaDescription} />
      <meta name="twitter:image" content={metaImage} />
      <meta name="twitter:site" content="@NoFeesApts" />
      <meta name="twitter:creator" content="@NoFeesApts" />

      {/* Additional SEO Meta Tags */}
      <meta name="author" content="NoFeesApts.com" />
      <meta name="robots" content={noindex ? "noindex, nofollow" : "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"} />
      <meta name="googlebot" content="index, follow" />
      <meta name="bingbot" content="index, follow" />
      
      {/* Geo Tags for Local SEO */}
      <meta name="geo.region" content="US-NY" />
      <meta name="geo.placename" content="New York City" />
      
      {/* Mobile & PWA */}
      <meta name="mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

      {/* Structured Data - Organization */}
      <script type="application/ld+json">
        {JSON.stringify(organizationSchema)}
      </script>

      {/* Structured Data - WebSite with SearchAction */}
      <script type="application/ld+json">
        {JSON.stringify(websiteSchema)}
      </script>

      {/* Structured Data - Custom */}
      {structuredData && (
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      )}

      {/* Structured Data - Breadcrumbs */}
      {breadcrumbSchema && (
        <script type="application/ld+json">
          {JSON.stringify(breadcrumbSchema)}
        </script>
      )}

      {/* Structured Data - FAQ */}
      {faqSchema && (
        <script type="application/ld+json">
          {JSON.stringify(faqSchema)}
        </script>
      )}

      {/* Structured Data - Article */}
      {articleSchema && (
        <script type="application/ld+json">
          {JSON.stringify(articleSchema)}
        </script>
      )}

      {/* Structured Data - Product */}
      {productSchema && (
        <script type="application/ld+json">
          {JSON.stringify(productSchema)}
        </script>
      )}
    </Helmet>
  );
};

export default SEO;
