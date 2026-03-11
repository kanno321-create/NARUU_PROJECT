import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = "https://hkkor.com";

  const staticPages = [
    { url: baseUrl, priority: 1.0 },
    { url: `${baseUrl}/home`, priority: 1.0 },
    { url: `${baseUrl}/about`, priority: 0.8 },
    { url: `${baseUrl}/about/greeting`, priority: 0.6 },
    { url: `${baseUrl}/about/organization`, priority: 0.6 },
    { url: `${baseUrl}/about/branches`, priority: 0.6 },
    { url: `${baseUrl}/about/certificates`, priority: 0.6 },
    { url: `${baseUrl}/about/location`, priority: 0.7 },
    { url: `${baseUrl}/products`, priority: 0.9 },
    { url: `${baseUrl}/products/steel-enclosure`, priority: 0.7 },
    { url: `${baseUrl}/products/stainless-enclosure`, priority: 0.7 },
    { url: `${baseUrl}/products/meter-box`, priority: 0.7 },
    { url: `${baseUrl}/products/distribution-panel`, priority: 0.7 },
    { url: `${baseUrl}/products/ev-panel`, priority: 0.7 },
    { url: `${baseUrl}/products/solar-panel`, priority: 0.7 },
    { url: `${baseUrl}/estimate`, priority: 0.9 },
    { url: `${baseUrl}/support`, priority: 0.7 },
    { url: `${baseUrl}/support/notice`, priority: 0.5 },
    { url: `${baseUrl}/support/faq`, priority: 0.6 },
    { url: `${baseUrl}/support/contact`, priority: 0.7 },
  ];

  return staticPages.map((page) => ({
    url: page.url,
    lastModified: new Date(),
    changeFrequency: "monthly" as const,
    priority: page.priority,
  }));
}
