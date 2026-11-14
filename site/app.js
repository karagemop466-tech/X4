// Static research dashboard: intentionally no invented/live NFL data or external data calls.
const links=[...document.querySelectorAll('.sidebar nav a')];
const sections=[...document.querySelectorAll('main section[id]')];
const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting){links.forEach(link=>link.classList.toggle('active',link.hash===`#${entry.target.id}`));}}},{rootMargin:'-20% 0px -70% 0px'});
sections.forEach(section=>observer.observe(section));
