pipeline {
    agent any

    environment {
        DEPLOY_DIR = "/opt/app-deploy"
        VENV_NAME = "venv"
    }

    stages {
        stage('1. Dependency Management') {
            steps {
                echo "==> Verificando requirements.txt..."
                sh '''
                    if [ ! -f "requirements.txt" ]; then
                        echo "Error: No se encontró requirements.txt"
                        exit 1
                    fi
                    cat requirements.txt
                '''
            }
        }

        stage('2. Build') {
            steps {
                echo "==> Configurando entorno e instalando dependencias..."
                sh '''
                    python3 -m venv ${VENV_NAME}
                    . ${VENV_NAME}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('3. Test') {
            steps {
                echo "==> Ejecutando pruebas básicas..."
                sh '''
                    . ${VENV_NAME}/bin/activate
                    python3 -c "import flask; print('Flask OK')"
                    test -f app.py
                    test -f init_db.py
                    echo "Pruebas superadas con éxito."
                '''
            }
        }

	stage('4. Deploy (Simulado)') {
	    steps {
		echo "==> Desplegando en Kali Linux..."
		sh '''
		    mkdir -p $HOME/app-deploy
		    cp app.py init_db.py requirements.txt $HOME/app-deploy/
		    echo "Despliegue completado en $HOME/app-deploy"
		    ls -la $HOME/app-deploy
		'''
	    }
	}

    }

    post {
        success {
            echo "Pipeline finalizado correctamente."
        }
        failure {
            echo "El pipeline falló."
        }
    }
}
