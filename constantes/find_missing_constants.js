const fs = require('fs');
const path = require('path');

const constantsFile = '/Users/claudiograsso/Documents/Sentiance/Crawl4AI/traductor_constantes.js';
const documentationDir = '/Users/claudiograsso/Documents/Sentiance/Crawl4AI/scraped_site';

function extractJSConstants() {
    const content = fs.readFileSync(constantsFile, 'utf8');
    const regex = /export const (\w+) = \{([\s\S]+?)\};/g;
    let match;
    const allConstants = new Set();
    while ((match = regex.exec(content)) !== null) {
        const entriesText = match[2];
        const keys = entriesText.split('\n')
            .map(line => line.trim())
            .filter(line => line && !line.startsWith('//'))
            .map(line => {
                const keyMatch = line.match(/^(\w+):/);
                return keyMatch ? keyMatch[1] : null;
            })
            .filter(key => key !== null);
        keys.forEach(k => allConstants.add(k));
    }
    return allConstants;
}

function findPotentialConstantsInDocs() {
    const docFiles = fs.readdirSync(documentationDir)
        .filter(file => file.endsWith('.md'))
        .map(file => path.join(documentationDir, file));

    const potentialConstants = new Map(); // Group -> Set of keys

    docFiles.forEach(file => {
        const content = fs.readFileSync(file, 'utf8');

        // Pattern 1: Enum-like blocks (e.g., AGGRESSIVE_DRIVER, BAR_GOER in SegmentType)
        // Look for lines starting with | "CONSTANT" or CONSTANT, or SENTSegmentTypeConstant

        // Find code blocks or lists that look like enums
        // We'll use a regex to find uppercase words that look like constants
        const lines = content.split('\n');
        let currentHeader = '';

        lines.forEach(line => {
            if (line.startsWith('#') || line.startsWith('##')) {
                currentHeader = line.replace(/#/g, '').trim();
            }

            // Match uppercase words with underscores, at least 3 chars
            const matches = line.match(/\b[A-Z][A-Z0-9_]{2,}\b/g);
            if (matches) {
                matches.forEach(m => {
                    // Filter out some common words that are not constants
                    if (['SENTIANCE', 'SDK', 'API', 'URL', 'ID', 'UTC', 'MB', 'GB', 'GPS', 'OSM', 'IOS', 'ANDROID'].includes(m)) return;

                    if (!potentialConstants.has(currentHeader)) {
                        potentialConstants.set(currentHeader, new Set());
                    }
                    potentialConstants.get(currentHeader).add(m);
                });
            }
        });
    });
    return potentialConstants;
}

function runComparison() {
    const jsConstants = extractJSConstants();
    const docConstantsMap = findPotentialConstantsInDocs();

    console.log("Checking for missing constants in traductor_constantes.js...");

    const missing = [];

    // We only care about headers that represent the categories we have in JS
    const relevantCategories = [
        'SegmentType', 'SENTSegmentType', 'TransportMode', 'SENTTransportMode',
        'VenueType', 'SENTVenueType', 'EventType', 'SENTTimelineEventType',
        'OccupantRole', 'SENTOccupantRole', 'SemanticTime', 'SENTSemanticTime',
        'VenueSignificance', 'SENTVenueSignificance', 'SegmentCategory', 'SENTSegmentCategory',
        'SegmentSubcategory', 'SENTSegmentSubCategory', 'HarshDrivingEventType'
    ];

    for (const [header, constants] of docConstantsMap.entries()) {
        const isRelevant = relevantCategories.some(cat => header.toLowerCase().includes(cat.toLowerCase()));
        if (!isRelevant) continue;

        for (let constant of constants) {
            // Normalize constant: remove SENTSegmentType prefix for iOS comparison
            let normalized = constant;
            if (constant.startsWith('SENTSegmentType')) normalized = constant.replace('SENTSegmentType', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);
            if (constant.startsWith('SENTTransportMode')) normalized = constant.replace('SENTTransportMode', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);
            if (constant.startsWith('SENTVenueType')) normalized = constant.replace('SENTVenueType', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);
            if (constant.startsWith('SENTOccupantRole')) normalized = constant.replace('SENTOccupantRole', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);
            if (constant.startsWith('SENTVenueSignificance')) normalized = constant.replace('SENTVenueSignificance', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);
            if (constant.startsWith('SENTSemanticTime')) normalized = constant.replace('SENTSemanticTime', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);
            if (constant.startsWith('SENTSegmentCategory')) normalized = constant.replace('SENTSegmentCategory', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);
            if (constant.startsWith('SENTSegmentSubCategory')) normalized = constant.replace('SENTSegmentSubCategory', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);
            if (constant.startsWith('SENTTimelineEventType')) normalized = constant.replace('SENTTimelineEventType', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);
            if (constant.startsWith('SENTHarshDrivingEventType')) normalized = constant.replace('SENTHarshDrivingEventType', '').replace(/([A-Z])/g, '_$1').toUpperCase().substring(1);

            if (!jsConstants.has(normalized) && !jsConstants.has(constant)) {
                missing.push({ category: header, docValue: constant, normalizedValue: normalized });
            }
        }
    }

    if (missing.length === 0) {
        console.log("No missing constants found.");
    } else {
        console.log("MISSING CONSTANTS (In docs but not in traductor_constantes.js):");
        const grouped = {};
        missing.forEach(m => {
            if (!grouped[m.category]) grouped[m.category] = [];
            grouped[m.category].push(`${m.docValue}${m.docValue !== m.normalizedValue ? ' (-> ' + m.normalizedValue + ')' : ''}`);
        });

        for (const [cat, list] of Object.entries(grouped)) {
            console.log(`\nCategory: ${cat}`);
            [...new Set(list)].sort().forEach(item => console.log(`  - ${item}`));
        }
    }
}

runComparison();
