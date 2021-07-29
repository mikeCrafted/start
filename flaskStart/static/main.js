/*
    TODO:
    #) get package verions either from pip website or use api
    #) write function to validate if last el of array has data, otherwise disalble button
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
            useCsrf: true,
            forms: [
                { 
                    // https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/03-Forms-and-Validation/forms.py
                    // https://flask-wtf.readthedocs.io/en/0.15.x/quickstart/#creating-forms
                    name: 'RegistrationForm',
                    lastFieldFilled: true,
                    fields: [
                        { name: 'username', validators: [] },
                        { name: 'email', validators: [] },
                        { name: 'password', validators: [] },
                        { name: 'confirm_password', validators: ["EqualsTo('password')"] }
                    ] 
                },
            ],
        },
        addWtForms: false,
        emails: false,
    },
    methods: {
        removeElementFromDatasource: function(datasource, element) {
            datasource.splice(datasource.indexOf(element), 1);
        },
        extendArrayByElement: function(array, element) {
            array.splice(array.length, 1, element);
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
                this.extendArrayByElement(this.wtForms.forms, { 
                    name: 'LoginForm', 
                    fields: [
                        { name: 'email', validators: [] },
                        { name: 'password', validators: [] },
                    ]  
                });
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
        checkForms() {
            const package = [ { name: 'Flask-WTF', version: '2.3.3', type: '==' } ];
            handlePackages(this.requirements, package, this.wtForms.show);
        },
    },
    computed: {
        checkForms() {
            return this.wtForms.show;
        },
        normalizeFormName() {
            return this.wtForms.forms.map(function(form) {
                let inputValue = form.name.trim();
                if (inputValue.includes(' ') && inputValue.length > 0) {
                    let components = form.name.split(' ');
                    let lastPart = components[components.length - 1];
                    components[components.length - 1] = lastPart[0].toUpperCase() + lastPart.slice(1);
                    components[0] = components[0][0].toUpperCase() + components[0].slice(1);
                    return form.name = components.join('');
                }
                else {
                    return form.name;
                }
            });
        }
    }
})

// Function to check if package is already included and add/delete
// requirements and packages are lists, condition is boolean
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