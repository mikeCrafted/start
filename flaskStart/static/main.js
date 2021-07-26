/*
    TODO:
    #) get package verions either from pip website or use api
*/

var app = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        projectName: '',
        addDatabase: false,
        addAuthSys: false,
        batStarter: false,
        blueprints: false,
        virtEnv: {
            show: false,
            name: 'venv',
            params: [
                { name: 'systemSitePackages', value: false },
                { name: 'pip', value: true },
                { name: 'clear', value: false }
            ],
        },
        requirements: [
            { name: 'flask', version: '2.0.1', type: '=='},
        ],
        dbType: '',
        userTableFields: [
            { name: 'id', pk: true, nullable: false, type: 'Integer', unique: true },
            { name: 'name', pk: false, nullable: false, type: 'String', unique: true },
            { name: 'email', pk: false, nullable: false, type: 'String', unique: true },
            { name: 'password', pk: false, nullable: false, type: 'String', unique: false }
        ],
        lastFieldFilled: true,
        loginView: 'login',
        wtForms: {
            show: false,
        },
    },
    methods: {
        removeElementFromDatasource: function(datasource, element) {
            datasource.splice(datasource.indexOf(element), 1);
        },
        addTableColumn: function() {
            this.userTableFields.splice(this.userTableFields.length, 1, {});
        },
        sendData: function() {
            fetch(`${window.origin}/create`, {
                method: "POST",
                body: JSON.stringify(this.$data),
                headers: new Headers({
                  "content-type": "application/json"
                })
            })
            .then(function (response) {
                if (response.status !== 200) {
                    alert(`Looks like there was a problem. Status code: ${response.status}`);
                    return;
                }
                
                response.json().then(function(data) {
                    
                });
                
            })
            .catch(function (error) {
                console.log("Fetch error: " + error);
            });
        },
    },
    watch: {
        userTableFields: {
            handler: function() {
                let lastEl = this.userTableFields[this.userTableFields.length - 1].name;
                if (lastEl === "" || lastEl === undefined) {
                    this.lastFieldFilled = false;
                }
                else {
                    this.lastFieldFilled = true;
                }
            },
            deep: true
        },
        dbType: function() {
            console.log(this.dbType);
        },
        addAuthSys: {
            handler: function() {
                const packages = [
                    { name: 'Flask-Login', version: '0.5.0', type: '==' }, 
                    { name: 'Bcrypt-Flask', version: '1.0.1', type: '==' }
                ];
                handlePackages(this.requirements, packages, this.addAuthSys);
            },
            deep: true
        },
        addDatabase: {
            handler: function() {
                const packages = [
                    { name: 'Flask-SQLAlchemy', version: '2.5.1', type: '=='}
                ];
                handlePackages(this.requirements, packages, this.addDatabase);
            },
            deep: true
        },
    }
})

// Function to check if package is already included and add/delete
function handlePackages(requirements, packages, condition) {
    if (condition === true) {
        // Looping over packages to add
        for (let i = 0; i < packages.length; i++) {
            let found = false;
            // Looking in requirements list
            requirements.forEach(package => package.name === packages[i].name ? found = true : package);
            if (!found) {
                requirements.push(packages[i]);
            }
        }
    }
    else {
        for (let i = 0; i < packages.length; i++) {
            requirements.forEach(package => package.name === packages[i].name ? requirements.splice(requirements.indexOf(package), 1) : package);
        }
    }
}