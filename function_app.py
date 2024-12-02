import json
import azure.functions as func
import logging
import pyodbc  # Make sure to install this package for database connection

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Connection string to your Azure SQL Database
# Update these with your actual database connection details
connection_string = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=tcp:localhost,1433;"
    "Database=Users;"  # This is your database name where employees data will be saved
    "Uid=sa;"
    "Pwd=YourStrongPassword!;"  # Ensure this is correct
)

@app.route(route="createEmployee", methods=["POST"])
def create_employee(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function to create employee processed a request.')
    logging.info(f"Raw request body: {req.get_body().decode('utf-8')}")

    try:
        req_body = req.get_json()
        # Extract employee details from the form
        employee_id = req_body.get('id')
        company = req_body.get('company')
        role = req_body.get('role')
        first_name = req_body.get('firstName')
        last_name = req_body.get('lastName')
        email = req_body.get('email')
        phone = req_body.get('phone')

        # Log the employee details (for debugging purposes)
        logging.info(f"Received employee details: {employee_id}, {company}, {role}, {first_name}, {last_name}, {email}, {phone}")

        # Insert employee details into the Employees table
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Employees (id, company, role, firstName, lastName, email, phone) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (employee_id, company, role, first_name, last_name, email, phone)
            )
            conn.commit()

        return func.HttpResponse(
            f"Employee {first_name} {last_name} saved successfully.",
            status_code=200,
            mimetype="application/json",
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Methods": "POST",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )

    except ValueError as e:
        logging.error(f"Failed to process request: {str(e)}")
        return func.HttpResponse("Invalid request.", status_code=400)
    except Exception as e:
        logging.error(f"Error saving employee: {str(e)}")
        return func.HttpResponse("An error occurred while saving employee details.", status_code=500)

@app.route(route="employees", methods=["GET"])
def get_employees(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function to get employees processed a request.')

    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Employees")
            rows = cursor.fetchall()

            # Prepare the result as a list of dictionaries
            employees = []
            for row in rows:
                employee = {
                    "id": row.id,
                    "company": row.company,
                    "role": row.role,
                    "firstName": row.firstName,
                    "lastName": row.lastName,
                    "email": row.email,
                    "phone": row.phone
                }
                employees.append(employee)

        return func.HttpResponse(
            json.dumps(employees),
            status_code=200,
            mimetype="application/json",
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )

    except pyodbc.Error as db_err:
        logging.error(f"Database error occurred while retrieving employees: {db_err}")
        return func.HttpResponse(
            f"Database error: {str(db_err)}",
            status_code=500
        )
    except Exception as e:
        logging.error(f"Unexpected error while retrieving employees: {str(e)}")
        return func.HttpResponse(
            "An unexpected error occurred while retrieving employee details.",
            status_code=500
        )
    

@app.route(route="updateEmployee", methods=["PUT"])
def update_employee(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function to update employee processed a request.')
    logging.info(f"Raw request body: {req.get_body().decode('utf-8')}")

    try:
        req_body = req.get_json()
        # Extract employee details from the form
        employee_id = req_body.get('id')
        company = req_body.get('company')
        role = req_body.get('role')
        first_name = req_body.get('firstName')
        last_name = req_body.get('lastName')
        email = req_body.get('email')
        phone = req_body.get('phone')

        # Log the employee details (for debugging purposes)
        logging.info(f"Received employee details: {employee_id}, {company}, {role}, {first_name}, {last_name}, {email}, {phone}")

        # Update employee details in the Employees table
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE Employees 
                SET company = ?, role = ?, firstName = ?, lastName = ?, email = ?, phone = ? 
                WHERE id = ?
                """,
                (company, role, first_name, last_name, email, phone, employee_id)
            )
            rows_affected = cursor.rowcount
            conn.commit()

        if rows_affected > 0:
            return func.HttpResponse(
                f"Employee {first_name} {last_name} updated successfully.",
                status_code=200,
                mimetype="application/json",
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Access-Control-Allow-Methods": "PUT",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
            )
        else:
            return func.HttpResponse(
                "Employee not found or no changes made.",
                status_code=404,
                mimetype="application/json"
            )

    except ValueError as e:
        logging.error(f"Failed to process request: {str(e)}")
        return func.HttpResponse("Invalid request.", status_code=400)
    except Exception as e:
        logging.error(f"Error updating employee: {str(e)}")
        return func.HttpResponse("An error occurred while updating employee details.", status_code=500)


@app.route(route="deleteEmployee", methods=["DELETE"])
def delete_employee(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function to delete employee processed a request.')
    
    try:
        # Extract employee IDs from the request body
        req_body = req.get_json()
        employee_ids = req_body.get('ids', [])

        if not employee_ids:
            return func.HttpResponse(
                "No employee IDs provided for deletion.",
                status_code=400,
                mimetype="application/json"
            )

        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()

            # Delete employees by their IDs
            for employee_id in employee_ids:
                cursor.execute(
                    "DELETE FROM Employees WHERE id = ?",
                    (employee_id,)
                )

            # Commit the transaction
            conn.commit()

        return func.HttpResponse(
            f"Successfully deleted {len(employee_ids)} employee(s).",
            status_code=200,
            mimetype="application/json",
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Methods": "DELETE",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )

    except ValueError as e:
        logging.error(f"Failed to process request: {str(e)}")
        return func.HttpResponse("Invalid request.", status_code=400)
    except Exception as e:
        logging.error(f"Error deleting employee(s): {str(e)}")
        return func.HttpResponse("An error occurred while deleting employee(s).", status_code=500)
