// Configuration
const CONFIG = {
    DATABASE_URL: 'family_graph.db', // SQLite database file
    REVEAL_DEPTH: 2, // Number of levels to reveal around authenticated user
    ADMIN_CENTER_PERSON: 'Ankit Bhatia', // Person to center admin view on
    // SHA-256 hash of admin password (default: "family2024")
    // To generate new hash: Open browser console and run:
    // crypto.subtle.digest('SHA-256', new TextEncoder().encode('YOUR_PASSWORD')).then(h => console.log(Array.from(new Uint8Array(h)).map(b => b.toString(16).padStart(2, '0')).join('')))
    ADMIN_PASSWORD_HASH: '071c00fa66449df33ffca0f3b71da9f9375eaf8feef471f348c9bac19e6f4914',
};

// Helper function to hash password
async function hashPassword(password) {
    const msgBuffer = new TextEncoder().encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    return Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
};

// Global state
let familyData = {
    people: new Map(), // id -> person object
    relationships: [],
    nameToId: new Map(),
};

let network = null;
let authenticatedUserId = null;
let revealedNodeIds = new Set();
let isAdminMode = false;
let db = null; // SQL.js database instance

// UI state for controls
let uiState = {
    layoutType: 'network', // 'network' or 'tree'
    currentDepth: 2,
    showParentEdges: true,
    showSpouseEdges: true,
    showSiblingEdges: true,
    showEdgeLabels: true,
    hideUnrevealedNodes: true
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadFamilyData();
    setupEventListeners();

    // Load dark mode preference
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
});

function setupEventListeners() {
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('darkModeToggle').addEventListener('click', toggleDarkMode);

    // Depth slider
    document.getElementById('depthSlider').addEventListener('input', updateDepthDisplay);
    document.getElementById('applyDepth').addEventListener('click', applyDepthChange);

    // Layout buttons
    document.getElementById('layoutNetwork').addEventListener('click', () => setLayout('network'));
    document.getElementById('layoutTree').addEventListener('click', () => setLayout('tree'));

    // Edge toggles
    document.getElementById('showParentEdges').addEventListener('change', () => toggleEdges('parent'));
    document.getElementById('showSpouseEdges').addEventListener('change', () => toggleEdges('spouse'));
    document.getElementById('showSiblingEdges').addEventListener('change', () => toggleEdges('sibling'));
    document.getElementById('showEdgeLabels').addEventListener('change', toggleEdgeLabels);
    document.getElementById('hideUnrevealedNodes').addEventListener('change', toggleHideUnrevealed);
}

// ============ DATA LOADING ============

async function loadFamilyData() {
    const statusEl = document.getElementById('loadingStatus');

    try {
        statusEl.textContent = 'Loading SQL.js library...';

        // Load SQL.js library from CDN
        const SQL = await initSqlJs({
            locateFile: file => `https://sql.js.org/dist/${file}`
        });

        statusEl.textContent = 'Loading family database...';

        // Fetch the database file
        const response = await fetch(CONFIG.DATABASE_URL);
        if (!response.ok) {
            throw new Error(`Failed to load database: ${response.status}`);
        }

        const buf = await response.arrayBuffer();
        db = new SQL.Database(new Uint8Array(buf));

        statusEl.textContent = 'Parsing family data...';

        // Load all people
        const peopleQuery = db.exec('SELECT id, name, name_lower FROM people');
        if (peopleQuery.length === 0) {
            throw new Error('No people found in database');
        }

        const peopleRows = peopleQuery[0];
        const peopleData = peopleRows.values;

        // Build people map
        for (const [id, name, name_lower] of peopleData) {
            familyData.people.set(id, {
                id,
                name,
                relationships: {
                    parent: [],
                    child: [],
                    wife: [],
                    husband: []
                }
            });
            familyData.nameToId.set(name_lower, id);
        }

        // Load all relationships
        const relQuery = db.exec('SELECT from_id, to_name, relationship_type FROM relationships');
        if (relQuery.length > 0) {
            const relRows = relQuery[0];
            const relData = relRows.values;

            for (const [fromId, toName, relType] of relData) {
                const person = familyData.people.get(fromId);
                if (person && person.relationships[relType]) {
                    person.relationships[relType].push(toName);
                }
            }
        }

        // Build sibling relationships
        buildSiblingRelationships();

        statusEl.textContent = 'Data loaded! Please login to view the graph.';
        console.log('Family data loaded:', {
            people: familyData.people.size,
            relationships: familyData.relationships.length
        });

    } catch (error) {
        console.error('Error loading family data:', error);
        statusEl.textContent = `Error: ${error.message}`;
        statusEl.style.color = '#e74c3c';
    }
}

function buildSiblingRelationships() {
    // Group people by parents to identify siblings
    const parentMap = new Map(); // parent -> [children]

    familyData.people.forEach((person, id) => {
        const parents = person.relationships.parent || [];
        if (parents.length > 0) {
            const parentKey = parents.sort().join('|');
            if (!parentMap.has(parentKey)) {
                parentMap.set(parentKey, []);
            }
            parentMap.get(parentKey).push(id);
        }
    });

    // Create sibling relationships
    parentMap.forEach(siblings => {
        if (siblings.length > 1) {
            for (let i = 0; i < siblings.length; i++) {
                for (let j = i + 1; j < siblings.length; j++) {
                    familyData.relationships.push({
                        from: siblings[i],
                        to: siblings[j],
                        type: 'sibling'
                    });
                }
            }
        }
    });
}

// Helper function to find all person IDs matching a name (ignoring number suffixes)
function findMatchingPersonIds(name) {
    const nameLower = name.toLowerCase().trim();
    const matchingIds = [];

    // Try exact match first
    const exactId = familyData.nameToId.get(nameLower);
    if (exactId) {
        matchingIds.push(exactId);
    }

    // Try with number suffixes (e.g., "name 1", "name 2", etc.)
    for (let i = 1; i <= 10; i++) {
        const numberedName = `${nameLower} ${i}`;
        const numberedId = familyData.nameToId.get(numberedName);
        if (numberedId) {
            matchingIds.push(numberedId);
        }
    }

    return matchingIds;
}

// ============ AUTHENTICATION ============

async function handleLogin(e) {
    e.preventDefault();

    const userName = document.getElementById('userName').value.trim();
    const parentName = document.getElementById('parentName').value.trim();
    const errorEl = document.getElementById('loginError');

    errorEl.textContent = '';

    // Check for admin mode
    if (userName.toLowerCase() === 'admin') {
        const hashedInput = await hashPassword(parentName);

        if (hashedInput === CONFIG.ADMIN_PASSWORD_HASH) {
        isAdminMode = true;
        authenticatedUserId = 'admin';
        revealAllNodes();
        showGraph();
        return;
        } else {
            errorEl.textContent = 'Invalid admin password.';
            return;
        }
    }

    // Reset admin mode for normal login
    isAdminMode = false;

    // Find all matching user IDs (including numbered variants)
    const userIds = findMatchingPersonIds(userName);
    const parentIds = findMatchingPersonIds(parentName);

    if (userIds.length === 0) {
        errorEl.textContent = `"${userName}" not found in family tree.`;
        return;
    }

    if (parentIds.length === 0) {
        errorEl.textContent = `"${parentName}" not found in family tree.`;
        return;
    }

    // Try to find a valid user-parent pair
    let validUserId = null;
    let validParentId = null;

    for (const userId of userIds) {
        const user = familyData.people.get(userId);

        for (const parentId of parentIds) {
            const parent = familyData.people.get(parentId);

            // Check if this user lists this parent
            const userHasParent = (user.relationships.parent || []).some(p => {
                const parentPersonId = familyData.nameToId.get(p.toLowerCase());
                return parentPersonId === parentId;
            });

            // Check if this parent lists this user as child
            const parentHasChild = (parent.relationships.child || []).some(c => {
                const childPersonId = familyData.nameToId.get(c.toLowerCase());
                return childPersonId === userId;
            });

            if (userHasParent && parentHasChild) {
                validUserId = userId;
                validParentId = parentId;
                break;
            }
        }

        if (validUserId) break;
    }

    if (!validUserId || !validParentId) {
        errorEl.textContent = 'Not a valid parent-child relationship. Please check the names.';
        if (userIds.length > 1 || parentIds.length > 1) {
            errorEl.textContent += ' (Multiple people with these names exist - none have the specified relationship.)';
        }
        return;
    }

    // Authentication successful
    authenticatedUserId = validUserId;
    revealNodes(validUserId, CONFIG.REVEAL_DEPTH);
    showGraph();
}

function handleLogout() {
    authenticatedUserId = null;
    revealedNodeIds.clear();
    isAdminMode = false;

    // Hide graph, show login
    document.getElementById('graphContainer').classList.remove('visible');
    document.getElementById('loginPanel').classList.remove('hidden');

    // Clear form
    document.getElementById('loginForm').reset();
    document.getElementById('loginError').textContent = '';
}

function revealAllNodes() {
    revealedNodeIds.clear();

    // Add all people to revealed set
    familyData.people.forEach((person, id) => {
        revealedNodeIds.add(id);
    });
}

function revealNodes(startNodeId, depth) {
    revealedNodeIds.clear();

    const queue = [{ id: startNodeId, depth: 0 }];
    const visited = new Set();

    while (queue.length > 0) {
        const { id, depth: currentDepth } = queue.shift();

        if (visited.has(id) || currentDepth > depth) continue;

        visited.add(id);
        revealedNodeIds.add(id);

        if (currentDepth < depth) {
            // Add all connected nodes
            const person = familyData.people.get(id);

            // Add parents
            (person.relationships.parent || []).forEach(parentName => {
                const parentId = familyData.nameToId.get(parentName.toLowerCase());
                if (parentId) queue.push({ id: parentId, depth: currentDepth + 1 });
            });

            // Add children
            (person.relationships.child || []).forEach(childName => {
                const childId = familyData.nameToId.get(childName.toLowerCase());
                if (childId) queue.push({ id: childId, depth: currentDepth + 1 });
            });

            // Add spouse
            const spouseNames = [
                ...(person.relationships.wife || []),
                ...(person.relationships.husband || [])
            ];
            spouseNames.forEach(spouseName => {
                const spouseId = familyData.nameToId.get(spouseName.toLowerCase());
                if (spouseId) queue.push({ id: spouseId, depth: currentDepth + 1 });
            });

            // Add siblings (from relationships array)
            familyData.relationships
                .filter(r => r.type === 'sibling' && (r.from === id || r.to === id))
                .forEach(r => {
                    const siblingId = r.from === id ? r.to : r.from;
                    queue.push({ id: siblingId, depth: currentDepth + 1 });
                });
        }
    }
}

// ============ GRAPH RENDERING ============

function showGraph() {
    document.getElementById('loginPanel').classList.add('hidden');
    document.getElementById('graphContainer').classList.add('visible');

    // Update user info display
    updateUserInfo();

    // Initialize slider to current depth
    if (!isAdminMode) {
        document.getElementById('depthSlider').value = uiState.currentDepth;
        updateDepthDisplay();
    }

    renderGraph();
}

function renderGraph() {
    const nodes = [];
    const edges = [];

    // Helper function to clean display names
    const cleanDisplayName = (name) => {
        // Remove number suffixes like " 2", " 1" from duplicate names
        return name.replace(/\s+\d+$/, '');
    };

    // Create nodes
    familyData.people.forEach((person, id) => {
        const isRevealed = revealedNodeIds.has(id);

        // Skip unrevealed nodes if hide option is enabled (only for non-admin)
        if (!isAdminMode && uiState.hideUnrevealedNodes && !isRevealed) {
            return;
        }
        const label = isRevealed ? cleanDisplayName(person.name) : id;

        nodes.push({
            id: id,
            label: label,
            color: isRevealed
                ? (isAdminMode ? '#f39c12' : (id === authenticatedUserId ? '#667eea' : '#95a5a6'))
                : '#ecf0f1',
            font: {
                color: isRevealed ? '#2c3e50' : '#bdc3c7',
                size: isRevealed ? 14 : 10
            }
        });
    });

    // Create edges from relationships
    familyData.people.forEach((person, id) => {
        // Parent-child edges
        if (uiState.showParentEdges) {
            (person.relationships.child || []).forEach(childName => {
                const childId = familyData.nameToId.get(childName.toLowerCase());
                if (childId) {
                    edges.push({
                        from: id,
                        to: childId,
                        color: { color: '#3498db' },
                        width: 2,
                        label: uiState.showEdgeLabels ? 'parent' : undefined
                    });
                }
            });
        }

        // Spouse edges (only add once)
        if (uiState.showSpouseEdges) {
            const spouseNames = [
                ...(person.relationships.wife || []),
                ...(person.relationships.husband || [])
            ];
            spouseNames.forEach(spouseName => {
                const spouseId = familyData.nameToId.get(spouseName.toLowerCase());
                if (spouseId && id < spouseId) { // Prevent duplicate edges
                    edges.push({
                        from: id,
                        to: spouseId,
                        color: { color: '#e74c3c' },
                        width: 2,
                        label: uiState.showEdgeLabels ? 'spouse' : undefined,
                        dashes: true
                    });
                }
            });
        }
    });

    // Add sibling edges
    if (uiState.showSiblingEdges) {
        familyData.relationships.forEach(rel => {
            if (rel.type === 'sibling') {
                edges.push({
                    from: rel.from,
                    to: rel.to,
                    color: { color: '#2ecc71' },
                    width: 1,
                    label: uiState.showEdgeLabels ? 'sibling' : undefined,
                    dashes: [5, 5]
                });
            }
        });
    }

    // Create vis network
    const container = document.getElementById('network');
    const data = { nodes, edges };
    const options = {
        layout: {
            hierarchical: uiState.layoutType === 'tree' ? {
                direction: 'UD',        // Up-Down (children below parents)
                sortMethod: 'directed',
                nodeSpacing: 150,
                levelSeparation: 200
            } : false
        },
        physics: {
            enabled: uiState.layoutType === 'network',
            barnesHut: {
                gravitationalConstant: -8000,
                springConstant: 0.04,
                springLength: 150
            },
            stabilization: {
                iterations: 200
            }
        },
        edges: {
            smooth: {
                type: 'continuous'
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 100
        }
    };

    if (network) {
        network.destroy();
    }

    network = new vis.Network(container, data, options);

    // Focus on authenticated user (or admin center person)
    if (isAdminMode) {
        const centerPersonId = familyData.nameToId.get(CONFIG.ADMIN_CENTER_PERSON.toLowerCase());
        setTimeout(() => {
            network.focus(centerPersonId || authenticatedUserId, {
                scale: 1.0,
                animation: true
            });
        }, 500);
    } else {
        setTimeout(() => {
            network.focus(authenticatedUserId, {
                scale: 1.0,
                animation: true
            });
        }, 500);
    }
}

// ============ UI CONTROLS ============

function updateDepthDisplay() {
    const slider = document.getElementById('depthSlider');
    const display = document.getElementById('depthValue');
    const value = parseInt(slider.value);

    if (value === 0) {
        display.textContent = 'Only me';
    } else if (value === 1) {
        display.textContent = '1 level';
    } else {
        display.textContent = `${value} levels`;
    }
}

function applyDepthChange() {
    if (isAdminMode) {
        alert('Depth control is disabled in admin mode (showing all nodes).');
        return;
    }

    const newDepth = parseInt(document.getElementById('depthSlider').value);
    uiState.currentDepth = newDepth;

    // Recalculate revealed nodes
    revealNodes(authenticatedUserId, newDepth);

    // Update UI
    updateUserInfo();

    // Re-render graph with new visibility
    renderGraph();
}

function setLayout(layoutType) {
    uiState.layoutType = layoutType;
    updateUserInfo();

    // Update button states
    document.getElementById('layoutNetwork').classList.toggle('active', layoutType === 'network');
    document.getElementById('layoutTree').classList.toggle('active', layoutType === 'tree');

    // Re-render with new layout
    renderGraph();
}

function toggleEdges(edgeType) {
    const checkbox = document.getElementById(`show${capitalize(edgeType)}Edges`);

    if (edgeType === 'parent') {
        uiState.showParentEdges = checkbox.checked;
    } else if (edgeType === 'spouse') {
        uiState.showSpouseEdges = checkbox.checked;
    } else if (edgeType === 'sibling') {
        uiState.showSiblingEdges = checkbox.checked;
    }

    // Re-render graph
    renderGraph();
}

function toggleEdgeLabels() {
    const checkbox = document.getElementById('showEdgeLabels');
    uiState.showEdgeLabels = checkbox.checked;

    // Re-render to update edge labels
    renderGraph();
}

function toggleHideUnrevealed() {
    if (isAdminMode) return; // No effect in admin mode

    const checkbox = document.getElementById('hideUnrevealedNodes');
    uiState.hideUnrevealedNodes = checkbox.checked;

    // Update user info to reflect change
    updateUserInfo();

    // Re-render graph
    renderGraph();
}

function updateUserInfo() {
    if (isAdminMode) {
        document.getElementById('userInfo').innerHTML = `
            <strong>🔓 Admin Mode</strong>
            <br>Showing all ${familyData.people.size} family members
        `;
        // Hide depth control in admin mode
        document.querySelector('.control-section:has(#depthSlider)').style.display = 'none';
        document.querySelector('.control-section:has(#hideUnrevealedNodes)').style.display = 'none';
    } else {
        const authenticatedPerson = familyData.people.get(authenticatedUserId);
        document.getElementById('userInfo').innerHTML = `
            <strong>Logged in as:</strong>
            ${authenticatedPerson.name}
            <br>
            ${revealedNodeIds.size} of ${familyData.people.size}
            <br>
            (${uiState.currentDepth} levels from you)
        `;
        // Show depth control in user mode
        document.querySelector('.control-section:has(#depthSlider)').style.display = 'block';
        document.querySelector('.control-section:has(#hideUnrevealedNodes)').style.display = 'block';
    }
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ============ DARK MODE ============

function toggleDarkMode() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}
